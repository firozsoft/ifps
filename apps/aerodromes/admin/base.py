from apps.general.admin.base import BaseExportableImportableModel


class AerodromePropertiesAdmin(BaseExportableImportableModel):
    autocomplete_fields = ["aerodrome"]
