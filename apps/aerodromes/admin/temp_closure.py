from django.contrib import admin

from apps.aerodromes.admin.resources import TempClosureResource
from apps.aerodromes.models.temp_closure import TemporaryClosure

from .base import AerodromePropertiesAdmin


@admin.register(TemporaryClosure)
class TemporaryClosureAdmin(AerodromePropertiesAdmin):
    resource_classes = [TempClosureResource]
