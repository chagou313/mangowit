from django.contrib import admin

from .models import NewsFetchRun, NewsItem


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published_at", "is_hidden")
    list_filter = ("is_hidden", "source")
    list_editable = ("is_hidden",)
    search_fields = ("title", "summary", "source")
    actions = ["hide", "show"]

    @admin.action(description="隐藏所选资讯")
    def hide(self, request, queryset):
        queryset.update(is_hidden=True)

    @admin.action(description="重新显示所选资讯")
    def show(self, request, queryset):
        queryset.update(is_hidden=False)


@admin.register(NewsFetchRun)
class NewsFetchRunAdmin(admin.ModelAdmin):
    list_display = ("started_at", "finished_at", "added", "error")
