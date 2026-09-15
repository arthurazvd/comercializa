from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Category, Product, Sale
from .serializers import (
    CategorySerializer, ProductSerializer, SaleSerializer, SaleCreateSerializer
)
from .services import dashboard_data


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer


class SaleListCreateView(generics.ListCreateAPIView):
    queryset = Sale.objects.prefetch_related("items__product").order_by("-created_at")

    def get_serializer_class(self):
        return SaleCreateSerializer if self.request.method == "POST" else SaleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class DashboardView(APIView):
    def get(self, request):
        return Response(dashboard_data())
