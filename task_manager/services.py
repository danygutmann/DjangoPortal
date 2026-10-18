from django.core.exceptions import PermissionDenied
from django.db import transaction

from task_manager.models import Task, TaskComment, TaskHistory


def can_access_task(user, task):
    return user.has_perm("task_manager.view_all_tasks") or user.has_perm(
        "task_manager.administer_task_manager"
    ) or task.created_by_id == user.pk or task.assigned_to_id == user.pk


def require_permission(user, permission):
    if not (
        user.has_perm("task_manager.administer_task_manager")
        or user.has_perm(f"task_manager.{permission}")
    ):
        raise PermissionDenied("You do not have permission to perform this action.")


def visible_tasks(user):
    if not user.has_perm("task_manager.view_task") and not user.has_perm("task_manager.view_all_tasks"):
        return Task.objects.none()
    if user.has_perm("task_manager.view_all_tasks") or user.has_perm("task_manager.administer_task_manager"):
        return Task.objects.select_related("created_by", "assigned_to").all()
    if not user.has_perm("task_manager.access_task_manager"):
        return Task.objects.none()
    return Task.objects.select_related("created_by", "assigned_to").filter(
        models_q_user(user)
    )


def models_q_user(user):
    from django.db.models import Q

    return Q(created_by=user) | Q(assigned_to=user)


@transaction.atomic
def create_task(*, user, data):
    require_permission(user, "create_task")
    if data.get("assigned_to") is not None:
        require_permission(user, "assign_task")
    task = Task.objects.create(created_by=user, **data)
    TaskHistory.objects.create(task=task, actor=user, changes={"created": True})
    return task


@transaction.atomic
def update_task(*, user, task, data):
    require_permission(user, "edit_task")
    if not can_access_task(user, task):
        raise PermissionDenied("You do not have access to this task.")
    if "assigned_to" in data and data["assigned_to"] != task.assigned_to:
        require_permission(user, "assign_task")
    changes = {}
    for field, value in data.items():
        previous = getattr(task, f"{field}_id" if field == "assigned_to" else field)
        current = value.pk if field == "assigned_to" and value else value
        if previous != current:
            changes[field] = {"from": str(previous) if previous is not None else None,
                              "to": str(current) if current is not None else None}
            setattr(task, field, value)
    if changes:
        task.save()
        TaskHistory.objects.create(task=task, actor=user, changes=changes)
    return task


@transaction.atomic
def delete_task(*, user, task):
    require_permission(user, "delete_task")
    if not can_access_task(user, task):
        raise PermissionDenied("You do not have access to this task.")
    task.delete()


@transaction.atomic
def add_comment(*, user, task, body):
    require_permission(user, "comment_task")
    if not can_access_task(user, task):
        raise PermissionDenied("You do not have access to this task.")
    return TaskComment.objects.create(task=task, author=user, body=body)
