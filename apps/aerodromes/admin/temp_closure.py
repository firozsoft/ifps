from django.contrib import admin

from apps.aerodromes.models import TemporaryClosure


@admin.register(TemporaryClosure)
class TemporaryClosureAdmin(admin.ModelAdmin):
    pass
