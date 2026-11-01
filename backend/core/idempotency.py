"""Repetição segura de POST quando a resposta HTTP se perde após o commit.

O cliente reutiliza o mesmo Idempotency-Key em tentativas da *mesma* operação.
A chave fica registrada na transação do cadastro; a repetição devolve a
resposta original sem executar novamente venda, baixa ou criação.
"""
import hashlib
import json
import re

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from .models import IdempotencyRecord

KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{16,100}$')


class IdempotentCreateMixin:
    def _create_business_response(self, request, *args, **kwargs):
        """Hook for endpoints that need a custom response serializer.

        Keep ``create`` owned by this mixin so the idempotency transaction is
        never bypassed by a view-specific POST handler.
        """
        return super().create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        key = request.headers.get('Idempotency-Key', '')
        if not key:
            # Clientes antigos permanecem compatíveis durante a implantação.
            return self._create_business_response(request, *args, **kwargs)
        if not KEY_PATTERN.fullmatch(key):
            return Response({'detail': 'Chave de operação inválida.'}, status=status.HTTP_400_BAD_REQUEST)

        identity = request.user.pk if request.user.is_authenticated else None
        fingerprint = hashlib.sha256(json.dumps(
            request.data, sort_keys=True, ensure_ascii=False, cls=DjangoJSONEncoder,
        ).encode('utf-8')).hexdigest()

        # A restrição UNIQUE da chave serializa tentativas concorrentes. A criação
        # do marcador e a gravação do negócio fazem parte da MESMA transação.
        with transaction.atomic():
            record, created = IdempotencyRecord.objects.get_or_create(
                key=key,
                defaults={
                    'user_id': identity, 'path': request.path,
                    'request_hash': fingerprint,
                    'response_status': 0, 'response_body': {},
                },
            )
            if not created:
                if (record.user_id != identity or record.path != request.path
                        or record.request_hash != fingerprint):
                    return Response({'detail': 'Esta chave já foi utilizada em outra operação.'},
                                    status=status.HTTP_409_CONFLICT)
                return Response(record.response_body, status=record.response_status,
                                headers={'X-Idempotent-Replay': 'true'})

            response = self._create_business_response(request, *args, **kwargs)
            if response.status_code >= 400:
                # A rejected operation must not leave behind an idempotency key.
                transaction.set_rollback(True)
                return response
            record.response_status = response.status_code
            record.response_body = response.data
            record.save(update_fields=['response_status', 'response_body'])
            return response
