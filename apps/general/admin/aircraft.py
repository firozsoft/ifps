from django.contrib import admin

from apps.general.admin.base import BaseExportableImportableModel
from apps.general.admin.resources import AircraftResource
from apps.general.models.aircraft import Aircraft


@admin.register(Aircraft)
class AircraftAdmin(BaseExportableImportableModel):
    resource_classes = [AircraftResource]
    search_fields = ["type", "model", "manufacturer"]
    list_filter = ["variant", "engine_count"]
