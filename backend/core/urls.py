from django.urls import include, path
from .auth_views import HealthView, SessionStatusView, LoginView, LogoutView
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, SaleListCreateView,
    StockMovementListCreateView, DashboardView, SaleCancelView, OperationStatusView,
)

from .export_views import StockOverviewView, StockExportView, FinanceReportView, FinanceExportView

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)

urlpatterns = [
    path("health/", HealthView.as_view(), name="api-health"),
    path("auth/status/", SessionStatusView.as_view(), name="auth-status"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("", include(router.urls)),
    path("sales/", SaleListCreateView.as_view(), name="sales"),
    path("sales/<int:pk>/cancel/", SaleCancelView.as_view(), name="sale-cancel"),
    path("operations/<str:key>/", OperationStatusView.as_view(), name="operation-status"),
    path("stock-movements/", StockMovementListCreateView.as_view(), name="stock-movements"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("stock-overview/", StockOverviewView.as_view(), name="stock-overview"),
    path("stock-export/", StockExportView.as_view(), name="stock-export"),
    path("reports/finance/", FinanceReportView.as_view(), name="finance-report"),
    path("reports/finance/export/", FinanceExportView.as_view(), name="finance-export"),
]
