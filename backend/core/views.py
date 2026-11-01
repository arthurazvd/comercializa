from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.utils import timezone
from io import BytesIO
import re
import warnings
from PIL import Image, UnidentifiedImageError
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, ProductImage, Sale, StockMovement, StockLot, StockLotAllocation, IdempotencyRecord
from .idempotency import IdempotentCreateMixin
from .serializers import (
    CategorySerializer, ProductSerializer, SaleSerializer, SaleCreateSerializer,
    StockMovementSerializer, StockAdjustmentSerializer,
)
from .services import dashboard_data
from rest_framework import serializers


class CategoryViewSet(IdempotentCreateMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(IdempotentCreateMixin, viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("lots").all()
    serializer_class = ProductSerializer

    @action(detail=True, methods=['get', 'put', 'delete'], url_path='image', parser_classes=[MultiPartParser])
    def image(self, request, pk=None):
        product = self.get_object()
        if request.method == 'GET':
            record = get_object_or_404(ProductImage, product=product)
            response = HttpResponse(bytes(record.data), content_type='image/jpeg')
            response['Cache-Control'] = 'private, max-age=120'
            response['X-Content-Type-Options'] = 'nosniff'
            return response
        if request.method == 'DELETE':
            with transaction.atomic():
                ProductImage.objects.filter(product=product).delete()
                Product.objects.filter(pk=product.pk).update(image_updated_at=None)
            return Response({'has_image': False, 'image_updated_at': None})

        photo = request.FILES.get('image')
        if photo is None:
            return Response({'image': ['Envie uma imagem no campo image.']}, status=400)
        # A normalização é feita no navegador, mas o servidor valida novamente.
        # Não confiar apenas no content-type informado pelo cliente.
        if photo.size > 102400 or photo.size == 0:
            return Response({'image': ['A imagem deve ter no máximo 100 KB.']}, status=400)
        data = photo.read(102401)
        if len(data) > 102400 or not data.startswith(b'\xff\xd8\xff'):
            return Response({'image': ['Envie um arquivo JPEG válido de até 100 KB.']}, status=400)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as check:
                    if check.format != 'JPEG' or max(check.size) > 4096:
                        raise ValueError('Formato ou dimensões inválidas')
                    check.verify()
        except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError):
            return Response({'image': ['JPEG inválido ou dimensões acima de 4096 pixels.']}, status=400)
        code = re.sub(r'[^A-Za-z0-9_-]+', '-', product.sku or str(product.pk)).strip('-')[:70] or str(product.pk)
        filename = f'{code}.jpg'
        with transaction.atomic():
            ProductImage.objects.update_or_create(product=product, defaults={
                'data': data, 'size': len(data), 'filename': filename,
            })
            updated_at = timezone.now()
            Product.objects.filter(pk=product.pk).update(image_updated_at=updated_at)
        return Response({'has_image': True, 'image_updated_at': updated_at, 'filename': filename, 'size': len(data)})

    def perform_update(self, serializer):
        product = serializer.save()
        if product.image_updated_at:
            code = re.sub(r'[^A-Za-z0-9_-]+', '-', product.sku or str(product.pk)).strip('-')[:70] or str(product.pk)
            ProductImage.objects.filter(product_id=product.pk).update(filename=f'{code}.jpg')

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Este produto possui histórico de vendas ou estoque. Desative-o em vez de excluir."},
                status=status.HTTP_409_CONFLICT,
            )


class SaleListCreateView(IdempotentCreateMixin, generics.ListCreateAPIView):
    queryset = Sale.objects.prefetch_related("items__product").order_by("-created_at")

    def get_serializer_class(self):
        return SaleCreateSerializer if self.request.method == "POST" else SaleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class StockMovementListCreateView(IdempotentCreateMixin, generics.ListCreateAPIView):
    queryset = StockMovement.objects.select_related("product", "sale").prefetch_related("lot_allocations__lot", "received_lots").order_by("-created_at", "-id")

    def get_serializer_class(self):
        return StockAdjustmentSerializer if self.request.method == "POST" else StockMovementSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = serializer.save()
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class CancelSaleSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=3, max_length=255, trim_whitespace=True)


class SaleCancelView(APIView):
    """Estorno integral auditável, seguro contra reenvio/repetição.

    Registra a reversão financeira (não há gateway para devolver valores
    automaticamente) e recoloca cada unidade no estoque/lote de origem.
    """
    @transaction.atomic
    def post(self, request, pk):
        data = CancelSaleSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        sale = get_object_or_404(Sale.objects.select_for_update().prefetch_related('items'), pk=pk)
        if sale.canceled_at:
            # Um timeout da resposta anterior não deve criar outro estorno.
            return Response(SaleSerializer(sale).data,
                            headers={'X-Idempotent-Replay': 'true'})
        items = list(sale.items.all())
        original_movements = list(StockMovement.objects.filter(
            sale=sale, reason=StockMovement.Reason.SALE,
        ).prefetch_related('lot_allocations').order_by('product_id', 'pk'))
        by_product = {}
        for movement in original_movements:
            by_product.setdefault(movement.product_id, []).extend(movement.lot_allocations.all())

        for item in sorted(items, key=lambda row: row.product_id):
            product = Product.objects.select_for_update().get(pk=item.product_id)
            before = product.stock
            after = before + item.quantity
            if after > 2147483647:
                raise serializers.ValidationError({'detail': 'Saldo excede o limite permitido.'})
            updated = Product.objects.filter(pk=product.pk, stock=before).update(
                stock=F('stock') + item.quantity)
            if not updated:
                raise serializers.ValidationError({'detail': 'Estoque alterado. Tente novamente.'})
            movement = StockMovement.objects.create(
                product=product, sale=sale, delta=item.quantity,
                stock_before=before, stock_after=after,
                reason=StockMovement.Reason.REVERSAL,
                justification=StockMovement.Justification.RETURN,
                note=f'Estorno venda #{sale.pk}: {data.validated_data["reason"]}'[:255],
            )
            for allocation in by_product.get(product.pk, []):
                lot = StockLot.objects.select_for_update().get(pk=allocation.lot_id)
                StockLot.objects.filter(pk=lot.pk).update(quantity=F('quantity') + allocation.quantity)
                StockLotAllocation.objects.create(
                    movement=movement, lot=lot, quantity=allocation.quantity)

        sale.canceled_at = timezone.now()
        sale.cancellation_reason = data.validated_data['reason']
        sale.canceled_by = request.user if request.user.is_authenticated else None
        sale.save(update_fields=['canceled_at', 'cancellation_reason', 'canceled_by'])
        return Response(SaleSerializer(sale).data)


class OperationStatusView(APIView):
    """Permite confirmar um POST gravado quando a resposta HTTP não chegou."""
    def get(self, request, key):
        identity = request.user.pk if request.user.is_authenticated else None
        record = get_object_or_404(IdempotencyRecord, key=key, user_id=identity)
        return Response({
            'confirmed': True, 'path': record.path,
            'status': record.response_status, 'data': record.response_body,
        })


class DashboardView(APIView):
    def get(self, request):
        return Response(dashboard_data())
