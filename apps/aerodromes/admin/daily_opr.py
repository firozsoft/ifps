from django.contrib import admin

from apps.aerodromes.admin.abstract import AerodromePropertiesAdmin
from apps.aerodromes.models import DailyOperationalHour


@admin.register(DailyOperationalHour)
class DailyOperationalHourAdmin(AerodromePropertiesAdmin):
    pass
