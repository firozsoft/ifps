from django.contrib import admin

from apps.airspaces.models import FIR


@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    search_fields = ("four_letters",)
