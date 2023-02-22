from django.contrib import admin

from apps.aerodromes.models import RWY


@admin.register(RWY)
class CurfewAdmin(admin.ModelAdmin):
    autocomplete_fields = ["aerodrome"]
