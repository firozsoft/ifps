from django.contrib import admin

from apps.routes.models import SidStar


@admin.register(SidStar)
class SidStarAdmin(admin.ModelAdmin):
    search_fields = ("name", "plain_language_name", "aerodrome")
    list_display = ("name", "plain_language_name", "nav_aid", "type", "is_active")
    list_editable = ("is_active",)
    list_filter = ("nav_aid__type", "type", "is_active")
