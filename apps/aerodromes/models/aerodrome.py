from django.core.validators import MinLengthValidator
from django.db import models

from apps.general.models import BasePoint
from core.utils.choices import AerodromeFlightType, AerodromeType, YesNo


class Aerodrome(BasePoint):
    """
    Aerodrome is a point itself and has following attrs:
        name: Aerodrome name in plain language (from base_model)
        type: Is it a heliport or airport, etc.
        ifr_vfr: Accepts ifr or vfr or both flight types
        aur: Is the aerodrome available on request when it is supposed to be closed
    """

    indicator = models.CharField(
        "ICAO Four Letters",
        max_length=4,
        unique=True,
        validators=[MinLengthValidator(4)],
    )
    iatacode = models.CharField("IATA Code", max_length=50, null=True, blank=True)
    type = models.CharField(
        "Aerodrome Type",
        max_length=8,
        choices=AerodromeType.choices,
        default=AerodromeType.AIRPORT,
        help_text=f"Choices: {', '.join(tp[1] for tp in AerodromeType.choices)}",
    )
    ifr_vfr = models.CharField(
        "IFR/VFR Flight Operation",
        max_length=7,
        choices=AerodromeFlightType.choices,
        default=AerodromeFlightType.IFR_VFR,
        help_text=f"Choices: {', '.join(tp[1] for tp in AerodromeFlightType.choices)}",
    )
    is_international = models.BooleanField(verbose_name="Is International", choices=YesNo, default=True)
    aur = models.BooleanField("Available Upon Request", choices=YesNo, default=True)

    class Meta(BasePoint.Meta):
        verbose_name = "Aerodrome"
        verbose_name_plural = "Aerodromes"
        ordering = ["indicator"]
        indexes = [models.Index(fields=["indicator"])]

    def __str__(self):
        return self.indicator
