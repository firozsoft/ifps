from django.contrib import admin

from apps.aerodromes.admin.abstract import AerodromePropertiesAdmin
from apps.aerodromes.models import Curfew


@admin.register(Curfew)
class CurfewAdmin(AerodromePropertiesAdmin):
    pass
