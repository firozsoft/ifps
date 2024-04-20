from django.contrib import admin

from apps.general.admin.base import BaseExportableImportableModel
from apps.routes.admin.resources import RouteSectionResource
from apps.routes.models.route_section import RouteSection


@admin.register(RouteSection)
class RouteSectionAdmin(BaseExportableImportableModel):
    search_fields = ["route", "point1", "point2"]
    list_display = ["route", "point1", "direction", "point2", "is_active"]
    list_editable = ["direction", "is_active"]
    autocomplete_fields = ["route", "point1", "point2"]
    resource_classes = [RouteSectionResource]
