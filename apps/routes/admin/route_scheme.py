from django.contrib import admin

from apps.general.admin.base import BaseExportableImportableModel
from apps.routes.admin.resources import RouteSchemeResource
from apps.routes.models.route_scheme import RouteScheme


@admin.register(RouteScheme)
class RouteSchemeAdmin(BaseExportableImportableModel):
    list_display = ["__str__"]
    list_select_related = True
    resource_classes = [RouteSchemeResource]
