# Module development

1. Create a Django app with module-owned models, migrations, API serializers,
   routes, services, administration, and tests.
2. Add `manifest.yaml` with `id`, `name`, `version`, `pages`, `navigation`, and
   a list of Django permission codenames. Paths must be absolute.
3. Register the manifest path in `MODULE_MANIFESTS` and install the app in
   `INSTALLED_APPS` in the deployment code. Only deployment-reviewed modules
   are eligible for discovery.
4. Implement the app's domain services and call them from the API and UI
   integration. Enforce permissions and object-level visibility on every
   server request.
5. Add migrations and tests, then run `python manage.py migrate` and
   `python manage.py sync_modules`.
6. Administrators enable/disable module records in Django admin. Disabling
   hides navigation and denies module API access without deleting module data.

The current registry validates the schema essentials and stores manifest
metadata; the initial frontend only contains a task page. New frontend routes
and deeper manifest validation must be implemented and reviewed as each module
is added.
