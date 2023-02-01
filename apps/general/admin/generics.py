from django.contrib import admin

from apps.general.models import FIR


@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    search_fields = ("four_letters",)


class BasePointAdmin(admin.ModelAdmin):
    readonly_fields = ["longitude", "latitude", "location"]
