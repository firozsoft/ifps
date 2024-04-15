from django.contrib import admin

from apps.general.admin.base import BaseExportableImportableModel
from apps.general.admin.resources import FIRResource
from apps.general.models.base import FIR


@admin.register(FIR)
class FIRAdmin(BaseExportableImportableModel):
    search_fields = ["indicator"]
    resource_classes = [FIRResource]
