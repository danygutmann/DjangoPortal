from rest_framework.permissions import BasePermission

from core.models import Module


class ActiveModulePermission(BasePermission):
    module_slug = None

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.has_perm(f"{self.module_slug}.access_task_manager")
            and Module.objects.filter(slug=self.module_slug, enabled=True).exists()
        )
