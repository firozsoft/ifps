from django.db import models

from core.utils.choices import YesNo

from .base import AerodromeProperties


class Curfew(AerodromeProperties):
    """Some Aerodromes have Curfew-Time"""

    # Fields that could be in STS
    hosp = models.BooleanField("Hospital", choices=YesNo, default=True)
    head = models.BooleanField("Head Flight", choices=YesNo, default=True)
    sar = models.BooleanField("SAR(search and rescue)", choices=YesNo, default=True)
    ffr = models.BooleanField("Fire-Fighting", choices=YesNo, default=True)
    hazmat = models.BooleanField("Hazardous Materials", choices=YesNo, default=True)
    med_evac = models.BooleanField("Medical Evacuation", choices=YesNo, default=True)
    # Fields that could be in RMK
    sm = models.BooleanField("SM Flight", choices=YesNo, default=True)
    emergency = models.BooleanField("Emergency", choices=YesNo, default=True)
    scramble = models.BooleanField("Scramble", choices=YesNo, default=True)
    delayed_sch_flight = models.BooleanField("Delayed Schedule Flight", choices=YesNo, default=True)
    military_il76 = models.BooleanField("Military IL76", choices=YesNo, default=True)
    curfew_coordinated = models.BooleanField(
        "Curfew Coordinated", choices=YesNo, default=True
    )

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Curfew"
        verbose_name_plural = "Curfews"

    @property
    def acceptable_sts(self):
        """Curfew for flights with STS filled with one of the following switches will be ignored"""
        return [
            item.upper()
            for item in ("hosp", "head", "sar", "ffr", "hazmat", "med_evac")
            if self.__getattribute__(item)
        ]

    @property
    def acceptable_rmk(self):
        """Curfew will be ignored for flights with RMK filled with one of following fields verbose_name"""
        rmk_fields = (
            "sm",
            "emergency",
            "scramble",
            "delayed_sch_flight",
            "military_il76",
            "curfew_coordinated",
        )
        return [
            self._meta.get_field(field).verbose_name.upper()
            for field in rmk_fields
            if self.__getattribute__(field)
        ]
