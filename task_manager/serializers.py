from django.contrib.auth import get_user_model
from rest_framework import serializers

from task_manager.models import Task, TaskComment, TaskHistory


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.get_username", read_only=True)
    assigned_to = serializers.CharField(source="assigned_to.get_username", read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        source="assigned_to", queryset=get_user_model().objects.filter(is_active=True), allow_null=True,
        required=False, write_only=True
    )

    class Meta:
        model = Task
        fields = (
            "id", "title", "description", "status", "priority", "due_date",
            "created_by", "assigned_to", "assigned_to_id", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class TaskCommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.get_username", read_only=True)

    class Meta:
        model = TaskComment
        fields = ("id", "author", "body", "created_at")
        read_only_fields = fields


class TaskHistorySerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.get_username", read_only=True)

    class Meta:
        model = TaskHistory
        fields = ("id", "actor", "changes", "created_at")
