from django.contrib import admin

from apps.general.models.fids import FIDSData


@admin.register(FIDSData)
class FIDSAdmin(admin.ModelAdmin):
    autocomplete_fields = ("type_of_aircraft",)
