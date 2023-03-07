from django.contrib import admin

from apps.aerodromes.admin.abstract import AerodromePropertiesAdmin
from apps.aerodromes.models import Curfew
from apps.aerodromes.models.abstract import AerodromeProperties


@admin.register(Curfew)
class CurfewAdmin(AerodromePropertiesAdmin):
    fieldsets = (
        (
            None,
            {
                "fields": tuple(
                    field.name
                    for field in AerodromeProperties._meta.get_fields()
                    if field.editable
                )
            },
        ),
        (
            "Exception STS",
            {"fields": (("hosp", "head", "sar", "ffr", "hazmat", "medevac"),)},
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
