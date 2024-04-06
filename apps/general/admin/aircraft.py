from django.contrib import admin

from apps.general.models.aircraft import Aircraft


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    search_fields = ["type", "model", "manufacturer"]
    list_filter = ["variant", "engine_count"]
