from django.contrib import admin

from ..models.aerodrome_models import (Aerodrome, Curfew, DailyOperationalHour,
                                       TemporaryClosure, )


@admin.register(Aerodrome)
class AerodromeAdmin(admin.ModelAdmin):
    pass


@admin.register(Curfew, DailyOperationalHour, TemporaryClosure)
class AerodromePropertiesAdmin(admin.ModelAdmin):
    pass
