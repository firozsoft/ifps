from django.contrib import admin

from apps.aerodromes.models.abstract import AerodromeProperties


class AerodromePropertiesAdmin(admin.ModelAdmin):
    autocomplete_fields = ["aerodrome"]
