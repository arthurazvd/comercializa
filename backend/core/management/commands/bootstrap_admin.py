"""Cria a conta administradora no primeiro deploy sem precisar do Shell pago do Render.

A senha inicial não é redefinida nos próximos deploys.
"""
import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Cria somente o primeiro admin usando INITIAL_ADMIN_* em variáveis de ambiente.'

    def handle(self, *args, **options):
        username = os.getenv('INITIAL_ADMIN_USERNAME', '').strip()
        password = os.getenv('INITIAL_ADMIN_PASSWORD', '')
        email = os.getenv('INITIAL_ADMIN_EMAIL', '').strip()
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Administrador já existe: nenhuma senha alterada.')
            return
        if not username or not password:
            raise CommandError('Primeiro deploy: configure INITIAL_ADMIN_USERNAME e INITIAL_ADMIN_PASSWORD (Render > Environment).')
        if len(password) < 12:
            raise CommandError('INITIAL_ADMIN_PASSWORD deve ter pelo menos 12 caracteres.')
        if User.objects.filter(username=username).exists():
            raise CommandError('Usuário inicial já existe sem ser administrador. Escolha outro INITIAL_ADMIN_USERNAME.')
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS('Conta administradora inicial criada.'))
