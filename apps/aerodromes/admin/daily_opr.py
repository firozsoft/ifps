from django.contrib import admin

from apps.aerodromes.models import DailyOperationalHour


@admin.register(DailyOperationalHour)
class DailyOperationalHourAdmin(admin.ModelAdmin):
    pass
