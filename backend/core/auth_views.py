"""Autenticação por token para o frontend hospedado em outro domínio."""
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'ok'})


class SessionStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'authentication_required': settings.REQUIRE_AUTH,
            'authenticated': request.user.is_authenticated,
            'username': request.user.get_username() if request.user.is_authenticated else None,
        })


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        username = str(request.data.get('username', '')).strip()
        password = str(request.data.get('password', ''))
        if not username or not password:
            return Response({'detail': 'Informe usuário e senha.'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if not user or not user.is_active:
            return Response({'detail': 'Usuário ou senha incorretos.'}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'username': user.get_username()})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Sessão encerrada.'})
