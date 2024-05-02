from django.contrib import admin

from apps.aerodromes.admin.resources import CurfewResource
from apps.aerodromes.models.base import AerodromeProperties
from apps.aerodromes.models.curfew import Curfew

from .base import AerodromePropertiesAdmin


@admin.register(Curfew)
class CurfewAdmin(AerodromePropertiesAdmin):
    resource_classes = [CurfewResource]
    fieldsets = (
        (
            None,
            {
                "fields": tuple(
                    # ruff:noqa:SLF001
                    field.name
                    for field in AerodromeProperties._meta.get_fields()
                    if field.editable
                ),
            },
        ),
        (
            "Exception(s) as STS",
            {"fields": (("hosp", "head", "sar", "ffr", "hazmat", "med_evac"),)},
        ),
        (
            "Exception(s) as RMK",
            {
                "fields": (
                    (
                        "sm",
                        "emergency",
                        "scramble",
                        "delayed_sch_flight",
                        "military_il76",
                        "curfew_coordinated",
                    ),
                ),
            },
        ),
    )
