from django.contrib import admin

from apps.aerodromes.admin.resources import DailyOperationalHourResource
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.general.admin.base import BaseExportableImportableModel


@admin.register(DailyOperationalHour)
class DailyOperationalHourAdmin(BaseExportableImportableModel):
    resource_classes = [DailyOperationalHourResource]
