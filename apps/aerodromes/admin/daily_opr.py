from django.contrib import admin

from apps.aerodromes.models.daily_opr import DailyOperationalHour

from .base import AerodromePropertiesAdmin


@admin.register(DailyOperationalHour)
class DailyOperationalHourAdmin(AerodromePropertiesAdmin):
    pass
