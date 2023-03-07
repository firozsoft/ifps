from django.contrib import admin

from apps.general.models import FIDSData


@admin.register(FIDSData)
class FIDSAdmin(admin.ModelAdmin):
    autocomplete_fields = ("ac_type",)
