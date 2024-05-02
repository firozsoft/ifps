from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from django.contrib import admin
from import_export.admin import ExportMixin

from core.resources import LogEntryResource

admin.site.site_header = "IFPS Administration"
admin.site.site_title = "IFPS Site Admin"

# Unregister the LogEntry model from the admin
admin.site.unregister(LogEntry)


@admin.register(LogEntry)
class ExportableLogEntryAdmin(ExportMixin, LogEntryAdmin):
    resource_class = LogEntryResource
