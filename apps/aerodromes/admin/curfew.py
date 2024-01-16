from django.contrib import admin

from apps.aerodromes.models import AerodromeProperties, Curfew

from .base import AerodromePropertiesAdmin


@admin.register(Curfew)
class CurfewAdmin(AerodromePropertiesAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": tuple(
                    field.name for field in AerodromeProperties._meta.get_fields() if field.editable
                )
            },
        ),
        (
            "Exception STS",
            {"fields": (("hosp", "head", "sar", "ffr", "hazmat", "med_evac"),)},
        ),
        (
            "Exception RMK",
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
                )
            },
        ),
    )
