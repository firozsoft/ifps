from django.contrib import admin

from apps.aerodromes.admin.abstract import AerodromePropertiesAdmin
from apps.aerodromes.models import TemporaryClosure


@admin.register(TemporaryClosure)
class TemporaryClosureAdmin(AerodromePropertiesAdmin):
    pass
