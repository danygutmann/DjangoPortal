from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from rest_framework.test import APITestCase

from core.models import Module
from task_manager.models import Task


User = get_user_model()
TEST_PASSWORD = "Strong-password-123"


class TaskAPITests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="alice")
        self.user.set_password(TEST_PASSWORD)
        self.user.save()
        self.other = User.objects.create_user(username="bob")
        self.other.set_password(TEST_PASSWORD)
        self.other.save()
        self.module = Module.objects.create(
            slug="task_manager", name="Task manager", version="1.0.0",
            manifest={"permissions": ["task_manager.access_task_manager"]}, enabled=True,
        )
        self.grant(self.user, "access_task_manager", "view_task", "create_task", "edit_task", "comment_task")
        response = self.client.post("/api/v1/auth/login/", {
            "username": "alice", "password": TEST_PASSWORD,
        })
        self.assertEqual(response.status_code, 200)
        self.token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def grant(self, user, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label="task_manager", codename__in=codenames
        )
        user.user_permissions.add(*permissions)

    def test_module_requires_permission_and_authentication(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/api/v1/tasks/").status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)
        self.module.enabled = False
        self.module.save(update_fields=["enabled"])
        self.assertEqual(self.client.get("/api/v1/tasks/").status_code, 403)

    def test_create_and_retrieve_task(self):
        response = self.client.post("/api/v1/tasks/", {"title": "Plan release", "priority": "high"})
        self.assertEqual(response.status_code, 201)
        task_id = response.data["id"]
        self.assertEqual(response.data["created_by"], "alice")
        self.assertEqual(self.client.get(f"/api/v1/tasks/{task_id}/").status_code, 200)
        self.assertEqual(Task.objects.get(pk=task_id).created_by, self.user)

    def test_known_uuid_does_not_expose_another_users_task(self):
        task = Task.objects.create(title="Private", created_by=self.other, assigned_to=self.other)
        self.assertEqual(self.client.get(f"/api/v1/tasks/{task.pk}/").status_code, 404)

    def test_logout_revokes_bearer_token(self):
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/me/permissions/").status_code, 401)

    def test_task_update_writes_audit_history(self):
        self.grant(self.user, "view_all_tasks")
        task = Task.objects.create(title="Old", created_by=self.other)
        response = self.client.patch(f"/api/v1/tasks/{task.pk}/", {"title": "New"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(task.history.count(), 1)
        self.assertEqual(task.history.first().changes["title"]["to"], "New")

    def test_assignment_requires_explicit_permission(self):
        response = self.client.post("/api/v1/tasks/", {
            "title": "Assign me", "assigned_to_id": str(self.other.pk),
        })
        self.assertEqual(response.status_code, 403)

    def test_module_administrator_can_manage_tasks_without_individual_grants(self):
        self.user.user_permissions.clear()
        self.grant(self.user, "administer_task_manager")
        response = self.client.post("/api/v1/tasks/", {"title": "Admin task"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/v1/tasks/").status_code, 200)

    def test_search_filters_and_invalid_dates(self):
        Task.objects.create(title="Release plan", status="open", created_by=self.user)
        Task.objects.create(title="Other", status="done", created_by=self.user)
        response = self.client.get("/api/v1/tasks/?search=release&status=open")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Release plan")
        self.assertEqual(self.client.get("/api/v1/tasks/?due_before=not-a-date").status_code, 400)
