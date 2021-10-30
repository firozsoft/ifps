from django.contrib import admin

from ..models.others import FIR, NOTAM, Aircraft


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    pass


@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    pass


@admin.register(NOTAM)
class NOTAMAdmin(admin.ModelAdmin):
    pass
