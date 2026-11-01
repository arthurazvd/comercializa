"""Lançamentos manuais auditáveis: despesas e investimento em ativos.

Um lançamento é identificado e nunca apagado fisicamente. A anulação é uma
reversão lógica, preservando histórico e a rastreabilidade do saldo.
"""
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import FinancialEntry
from .idempotency import IdempotentCreateMixin
from .reports import filters_from_query


class FinancialEntrySerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)

    class Meta:
        model = FinancialEntry
        fields = ['id', 'kind', 'kind_display', 'category', 'category_display',
                  'description', 'amount', 'entry_date', 'created_at', 'voided_at']
        read_only_fields = ['id', 'kind_display', 'category_display', 'created_at', 'voided_at']

    def validate_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('O valor deve ser maior que zero.')
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Descreva o lançamento com pelo menos 3 caracteres.')
        return value


class FinancialEntriesView(IdempotentCreateMixin, generics.ListCreateAPIView):
    serializer_class = FinancialEntrySerializer
    queryset = FinancialEntry.objects.filter(voided_at__isnull=True)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.method == 'GET':
            filters = filters_from_query(self.request.query_params)
            qs = qs.filter(entry_date__gte=filters['start'], entry_date__lte=filters['end'])
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)


class FinancialEntryVoidView(APIView):
    def post(self, request, pk):
        entry = get_object_or_404(FinancialEntry, pk=pk)
        if entry.voided_at is not None:
            return Response(FinancialEntrySerializer(entry).data, headers={'X-Idempotent-Replay': 'true'})
        from django.db import transaction
        with transaction.atomic():
            entry = FinancialEntry.objects.select_for_update().get(pk=pk)
            if entry.voided_at is None:
                entry.voided_at = timezone.now()
                entry.voided_by = request.user if request.user.is_authenticated else None
                entry.save(update_fields=['voided_at', 'voided_by'])
        return Response(FinancialEntrySerializer(entry).data)
