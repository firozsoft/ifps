from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin

from apps.general.forms import BasePointForm


class BaseExportableImportableModel(ImportExportModelAdmin, ExportActionModelAdmin, admin.ModelAdmin):
    """Just to be the base class for all import/export-able models."""


class BasePointAdmin(BaseExportableImportableModel):
    form = BasePointForm
    # readonly_fields = ["longitude", "latitude", "location"]
    readonly_fields = ["longitude", "latitude"]
    list_filter = ["is_active", "is_fir_boundary", "fir"]
