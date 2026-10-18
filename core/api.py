from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from core.authentication import issue_token
from core.models import APISession, Module


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=256, write_only=True, trim_whitespace=False)


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()


class PermissionResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    permissions = serializers.ListField(child=serializers.CharField())


class AuthViewSet(viewsets.ViewSet):
    serializer_class = LoginSerializer

    @extend_schema(request=LoginSerializer, responses={200: LoginResponseSerializer, 401: None})
    @action(detail=False, methods=["post"], permission_classes=[AllowAny], throttle_classes=[LoginRateThrottle])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, **serializer.validated_data)
        if user is None:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        session = APISession.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(seconds=settings.API_SESSION_MAX_AGE),
        )
        return Response({"token": issue_token(session), "expires_at": session.expires_at}, status=status.HTTP_200_OK)

    @extend_schema(request=None, responses={204: None})
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        request.auth.revoked_at = timezone.now()
        request.auth.save(update_fields=["revoked_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ("slug", "name", "version", "manifest")


class ModuleViewSet(ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        deployed = set(settings.MODULE_MANIFESTS)
        visible_slugs = [
            module.slug for module in Module.objects.filter(enabled=True, slug__in=deployed)
            if (
                module.manifest.get("admin_permission")
                and self.request.user.has_perm(module.manifest["admin_permission"])
            ) or all(self.request.user.has_perm(permission) for permission in module.manifest.get("permissions", []))
        ]
        return Module.objects.filter(slug__in=visible_slugs, enabled=True).order_by("name")


class PermissionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PermissionResponseSerializer

    @extend_schema(responses=PermissionResponseSerializer)
    def get(self, request):
        permissions = sorted(request.user.get_all_permissions())
        return Response({"username": request.user.get_username(), "permissions": permissions})
