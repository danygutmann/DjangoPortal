from django.contrib import admin

from core.models import APISession, Module


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "version", "enabled", "updated_at")
    list_editable = ("enabled",)
    readonly_fields = ("slug", "name", "version", "manifest", "updated_at")


@admin.register(APISession)
class APISessionAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "revoked_at")
    readonly_fields = ("id", "user", "created_at", "expires_at", "revoked_at")
    def has_add_permission(self, request):
        return False
