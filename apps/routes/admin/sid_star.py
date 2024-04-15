from django.contrib import admin

from apps.general.admin.base import BaseExportableImportableModel
from apps.routes.admin.resources import SidStarResource
from apps.routes.models.sid_star import SidStar


@admin.register(SidStar)
class SidStarAdmin(BaseExportableImportableModel):
    search_fields = ["indicator", "plain_language_name", "aerodrome__indicator"]
    list_display = ["indicator", "plain_language_name", "navaid", "type", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["navaid__type", "type", "is_active"]
    autocomplete_fields = ["aerodrome", "point", "navaid"]
    resource_classes = [SidStarResource]
