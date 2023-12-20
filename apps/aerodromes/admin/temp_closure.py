from django.contrib import admin

from apps.aerodromes.models import TemporaryClosure

from .base import AerodromePropertiesAdmin


@admin.register(TemporaryClosure)
class TemporaryClosureAdmin(AerodromePropertiesAdmin):
    pass
