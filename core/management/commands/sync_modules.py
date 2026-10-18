from django.core.management.base import BaseCommand

from core.models import Module
from core.registry import installed_manifests


class Command(BaseCommand):
    help = "Validate deployed module manifests and synchronize module metadata."

    def handle(self, *args, **options):
        for slug, manifest in installed_manifests().items():
            defaults = {
                "name": manifest["name"],
                "version": str(manifest["version"]),
                "manifest": manifest,
            }
            module, created = Module.objects.update_or_create(slug=slug, defaults=defaults)
            if created:
                module.enabled = bool(manifest.get("default_enabled", False))
                module.save(update_fields=["enabled"])
            self.stdout.write(f"{'Installed' if created else 'Updated'} module {slug}.")
