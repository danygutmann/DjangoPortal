from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from core.authentication import issue_token
from core.models import APISession, Module

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=256, write_only=True, trim_whitespace=False)


class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], permission_classes=[AllowAny], throttle_classes=[AnonRateThrottle])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        session = APISession.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(seconds=__import__("django.conf").conf.settings.API_SESSION_MAX_AGE),
        )
        return Response({"token": issue_token(session), "expires_at": session.expires_at}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        request.auth.revoked_at = timezone.now()
        request.auth.save(update_fields=["revoked_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ("slug", "name", "version", "manifest")


class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return [
            module for module in Module.objects.filter(enabled=True).order_by("name")
            if all(self.request.user.has_perm(permission) for permission in module.manifest.get("permissions", []))
        ]


class PermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        permissions = sorted(request.user.get_all_permissions())
        return Response({"username": request.user.get_username(), "permissions": permissions})
