from django.db.models.deletion import ProtectedError
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Sale, StockMovement
from .serializers import (
    CategorySerializer, ProductSerializer, SaleSerializer, SaleCreateSerializer,
    StockMovementSerializer, StockAdjustmentSerializer,
)
from .services import dashboard_data


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
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


class SaleListCreateView(generics.ListCreateAPIView):
    queryset = Sale.objects.prefetch_related("items__product").order_by("-created_at")

    def get_serializer_class(self):
        return SaleCreateSerializer if self.request.method == "POST" else SaleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class StockMovementListCreateView(generics.ListCreateAPIView):
    queryset = StockMovement.objects.select_related("product", "sale").prefetch_related("lot_allocations__lot", "received_lots").order_by("-created_at", "-id")

    def get_serializer_class(self):
        return StockAdjustmentSerializer if self.request.method == "POST" else StockMovementSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = serializer.save()
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class DashboardView(APIView):
    def get(self, request):
        return Response(dashboard_data())
