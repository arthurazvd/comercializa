"""Permissão central: proteger toda a API fora do modo local de desenvolvimento."""
from django.conf import settings
from rest_framework.permissions import BasePermission


class RequireAuthInProduction(BasePermission):
    message = 'É necessário entrar no Comercializa para acessar estes dados.'

    def has_permission(self, request, view):
        return not settings.REQUIRE_AUTH or bool(request.user and request.user.is_authenticated)
