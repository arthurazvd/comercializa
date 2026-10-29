from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, SaleListCreateView,
    StockMovementListCreateView, DashboardView,
)

from .export_views import StockOverviewView, StockExportView, FinanceReportView, FinanceExportView

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("sales/", SaleListCreateView.as_view(), name="sales"),
    path("stock-movements/", StockMovementListCreateView.as_view(), name="stock-movements"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("stock-overview/", StockOverviewView.as_view(), name="stock-overview"),
    path("stock-export/", StockExportView.as_view(), name="stock-export"),
    path("reports/finance/", FinanceReportView.as_view(), name="finance-report"),
    path("reports/finance/export/", FinanceExportView.as_view(), name="finance-export"),
]
