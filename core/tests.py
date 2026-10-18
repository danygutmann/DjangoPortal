from django.core.management import call_command
from django.test import TestCase

from core.models import Module
from core.registry import installed_manifests


class ModuleRegistryTests(TestCase):
    def test_installed_manifest_is_validated_and_synchronized(self):
        manifests = installed_manifests()
        self.assertIn("task_manager", manifests)
        call_command("sync_modules", stdout=open("/dev/null", "w"))
        module = Module.objects.get(slug="task_manager")
        self.assertTrue(module.enabled)
        module.enabled = False
        module.save(update_fields=["enabled"])
        call_command("sync_modules", stdout=open("/dev/null", "w"))
        module.refresh_from_db()
        self.assertFalse(module.enabled)
