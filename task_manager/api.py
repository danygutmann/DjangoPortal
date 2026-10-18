from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from core.models import Module
from task_manager.models import Task, TaskComment, TaskHistory
from task_manager.serializers import TaskCommentSerializer, TaskHistorySerializer, TaskSerializer
from task_manager.services import add_comment, can_access_task, create_task, delete_task, update_task, visible_tasks


class TaskAccessPermission(BasePermission):
    def has_permission(self, request, view):
        active_and_accessible = (
            request.user.is_authenticated
            and (
                request.user.has_perm("task_manager.administer_task_manager")
                or request.user.has_perm("task_manager.access_task_manager")
            )
            and Module.objects.filter(slug="task_manager", enabled=True).exists()
        )
        if not active_and_accessible:
            return False
        if request.user.has_perm("task_manager.administer_task_manager"):
            return True
        if view.action in {"list", "retrieve", "history"}:
            permission = "view_task"
        elif view.action == "comments":
            permission = "comment_task" if request.method == "POST" else "view_task"
        elif view.action == "create":
            permission = "create_task"
        elif view.action in {"update", "partial_update"}:
            permission = "edit_task"
        elif view.action == "destroy":
            permission = "delete_task"
        else:
            return False
        return request.user.has_perm(f"task_manager.{permission}")


class CommentInputSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, TaskAccessPermission]

    def get_queryset(self):
        queryset = visible_tasks(self.request.user)
        params = self.request.query_params
        search = params.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        status_filter = params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        priority_filter = params.get("priority")
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        due_before = params.get("due_before")
        if due_before:
            parsed = parse_date(due_before)
            if parsed is None:
                raise serializers.ValidationError({"due_before": "Use an ISO date (YYYY-MM-DD)."})
            queryset = queryset.filter(due_date__lte=parsed)
        due_after = params.get("due_after")
        if due_after:
            parsed = parse_date(due_after)
            if parsed is None:
                raise serializers.ValidationError({"due_after": "Use an ISO date (YYYY-MM-DD)."})
            queryset = queryset.filter(due_date__gte=parsed)
        if params.get("assigned_to_me") == "true":
            queryset = queryset.filter(assigned_to=self.request.user)
        scope = params.get("scope")
        if scope == "mine":
            queryset = queryset.filter(Q(created_by=self.request.user) | Q(assigned_to=self.request.user))
        elif scope == "all" and not (
            self.request.user.has_perm("task_manager.view_all_tasks")
            or self.request.user.has_perm("task_manager.administer_task_manager")
        ):
            raise PermissionDenied("You cannot view all tasks.")
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = create_task(user=request.user, data=serializer.validated_data)
        return Response(self.get_serializer(task).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        task = update_task(user=request.user, task=task, data=serializer.validated_data)
        return Response(self.get_serializer(task).data)

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        task = update_task(user=request.user, task=task, data=serializer.validated_data)
        return Response(self.get_serializer(task).data)

    def destroy(self, request, *args, **kwargs):
        delete_task(user=request.user, task=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "POST":
            serializer = CommentInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            comment = add_comment(user=request.user, task=task, body=serializer.validated_data["body"])
            return Response(TaskCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(TaskCommentSerializer(TaskComment.objects.filter(task=task), many=True).data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        task = self.get_object()
        return Response(TaskHistorySerializer(TaskHistory.objects.filter(task=task), many=True).data)
