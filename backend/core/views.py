from django.db.models.deletion import ProtectedError
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Sale, StockMovement, StockLot, StockLotAllocation, IdempotencyRecord
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
