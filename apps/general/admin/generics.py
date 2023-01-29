from django.contrib import admin

from apps.general.models import FIR


@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class BasePointAdmin(admin.ModelAdmin):
    readonly_fields = ["latitude", "longitude", "location"]
