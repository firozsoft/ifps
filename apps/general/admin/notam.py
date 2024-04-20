from django.contrib import admin
from import_export.admin import ExportMixin

from apps.general.admin.resources import NotamResource
from apps.general.models.notam import Notam


@admin.register(Notam)
class NOTAMAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ["number"]
    autocomplete_fields = [
        "affected_aerodrome",
        "affected_firs",
        "affected_points",
        "affected_navaids",
        "affected_sidstars",
        "affected_route_sections",
    ]
    resource_classes = [NotamResource]
