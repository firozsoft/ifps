from django.contrib import admin

from apps.general.admin.base import BaseExportableImportableModel
from apps.general.admin.resources import NotamResource
from apps.general.models.notam import Notam


@admin.register(Notam)
class NOTAMAdmin(BaseExportableImportableModel):
    search_fields = ["number"]
    autocomplete_fields = ["relevant"]
    resource_classes = [NotamResource]
