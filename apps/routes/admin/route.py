# from django.contrib.gis import admin
from django.contrib import admin

from apps.general.admin.base import BaseExportableImportableModel
from apps.routes.admin.resources import RouteResource
from apps.routes.models.base import Route


@admin.register(Route)
class RouteAdmin(BaseExportableImportableModel):
    search_fields = ["indicator"]
    fields = [
        "indicator",
        "is_active",
    ]
    resource_classes = [RouteResource]
