from django.contrib import admin

from ..models.aerodromes import (Aerodrome, Curfew, DailyOperationalHour,
                                 TemporaryClosure,)


@admin.register(Aerodrome)
class AerodromeAdmin(admin.ModelAdmin):
    pass


@admin.register(Curfew)
class CurfewAdmin(admin.ModelAdmin):
    pass


@admin.register(DailyOperationalHour)
class DailyOperationalHourAdmin(admin.ModelAdmin):
    pass


@admin.register(TemporaryClosure)
class TemporaryClosureAdmin(admin.ModelAdmin):
    pass
