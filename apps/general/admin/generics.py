from django.contrib import admin

from apps.general.models import FIR


@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    pass
