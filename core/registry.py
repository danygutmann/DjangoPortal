from pathlib import Path
import re

import yaml
from django.conf import settings
from django.core.management.base import CommandError


REQUIRED_FIELDS = {"id", "name", "version", "pages", "navigation", "permissions"}
MODULE_ID = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
PERMISSION = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


def load_manifest(slug: str, path: Path) -> dict:
    try:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise CommandError(f"Cannot load module manifest '{slug}': {exc}") from exc
    if not isinstance(manifest, dict) or REQUIRED_FIELDS - manifest.keys():
        raise CommandError(f"Module manifest '{slug}' is missing required fields.")
    if (
        manifest["id"] != slug or not MODULE_ID.fullmatch(slug)
        or not isinstance(manifest["name"], str) or not manifest["name"].strip()
        or not isinstance(manifest["version"], str) or not manifest["version"].strip()
        or not isinstance(manifest["pages"], list) or not isinstance(manifest["navigation"], list)
    ):
        raise CommandError(f"Module manifest '{slug}' has invalid identity or navigation.")
    if not isinstance(manifest["permissions"], list) or not all(
        isinstance(permission, str) and PERMISSION.fullmatch(permission)
        for permission in manifest["permissions"]
    ):
        raise CommandError(f"Module manifest '{slug}' has invalid permissions.")
    if "admin_permission" in manifest and (
        not isinstance(manifest["admin_permission"], str)
        or not PERMISSION.fullmatch(manifest["admin_permission"])
    ):
        raise CommandError(f"Module manifest '{slug}' has invalid admin_permission.")
    paths = set()
    for page in manifest["pages"]:
        if (
            not isinstance(page, dict) or not isinstance(page.get("path"), str)
            or not page["path"].startswith("/") or not isinstance(page.get("name"), str)
            or not page["name"].strip() or page["path"] in paths
        ):
            raise CommandError(f"Module manifest '{slug}' contains an invalid page.")
        paths.add(page["path"])
    for item in manifest["navigation"]:
        if (
            not isinstance(item, dict) or not isinstance(item.get("label"), str)
            or not item["label"].strip() or not isinstance(item.get("path"), str)
            or item["path"] not in paths
        ):
            raise CommandError(f"Module manifest '{slug}' contains invalid navigation.")
    if "default_enabled" in manifest and not isinstance(manifest["default_enabled"], bool):
        raise CommandError(f"Module manifest '{slug}' has invalid default_enabled.")
    return manifest


def installed_manifests():
    return {
        slug: load_manifest(slug, path)
        for slug, path in settings.MODULE_MANIFESTS.items()
    }
