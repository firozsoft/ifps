from django.contrib import admin


class AerodromePropertiesAdmin(admin.ModelAdmin):
    autocomplete_fields = ["aerodrome"]
