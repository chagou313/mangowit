from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("body", "user", "target", "created_at", "is_hidden")
    list_filter = ("is_hidden", "created_at")
    search_fields = ("body", "user__username", "target")
    actions = ["hide", "unhide"]

    @admin.action(description="隐藏选中的评论")
    def hide(self, request, queryset):
        queryset.update(is_hidden=True)

    @admin.action(description="恢复显示选中的评论")
    def unhide(self, request, queryset):
        queryset.update(is_hidden=False)
