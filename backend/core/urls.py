from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, SaleListCreateView,
    StockMovementListCreateView, DashboardView,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("sales/", SaleListCreateView.as_view(), name="sales"),
    path("stock-movements/", StockMovementListCreateView.as_view(), name="stock-movements"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
