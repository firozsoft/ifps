from django.contrib import admin

from apps.aerodromes.models import DailyOperationalHour

from .base import AerodromePropertiesAdmin


@admin.register(DailyOperationalHour)
class DailyOperationalHourAdmin(AerodromePropertiesAdmin):
    pass
