from django.contrib import admin

from apps.routes.models.sid_star import SidStar


@admin.register(SidStar)
class SidStarAdmin(admin.ModelAdmin):
    search_fields = ("indicator", "plain_language_name", "aerodrome__indicator")
    list_display = ("indicator", "plain_language_name", "navaid", "type", "is_active")
    list_editable = ("is_active",)
    list_filter = ("navaid__type", "type", "is_active")
    autocomplete_fields = ("aerodrome", "point", "navaid")
