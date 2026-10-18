from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.api import AuthViewSet, ModuleViewSet, PermissionView
from core.views import health
from task_manager.api import TaskViewSet

router = DefaultRouter()
router.register("auth", AuthViewSet, basename="auth")
router.register("modules", ModuleViewSet, basename="modules")
router.register("tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include(router.urls)),
    path("api/v1/me/permissions/", PermissionView.as_view(), name="my-permissions"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
]
