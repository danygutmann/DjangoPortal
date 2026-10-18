from django.contrib import admin

from task_manager.models import Task, TaskComment, TaskHistory


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    readonly_fields = ("author", "body", "created_at")


class TaskHistoryInline(admin.TabularInline):
    model = TaskHistory
    extra = 0
    readonly_fields = ("actor", "changes", "created_at")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "created_by", "assigned_to", "due_date")
    list_filter = ("status", "priority")
    search_fields = ("title", "description")
    inlines = (TaskCommentInline, TaskHistoryInline)
