from django.contrib import admin

from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date", "group")
    empty_value_display = "-пусто-"


class GroupAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "description")
    search_fields = ("title",)


class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "text",)
    list_filter = ("author",)
    search_fields = ("author",)


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
