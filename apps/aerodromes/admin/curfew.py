from django.contrib import admin

from apps.aerodromes.models import Curfew


@admin.register(Curfew)
class CurfewAdmin(admin.ModelAdmin):
    pass
