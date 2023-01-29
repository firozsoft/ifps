from django.core.validators import MinLengthValidator
from django.db import models

from apps.general.models.abstracts import BasePoint
from apps.utils.choices import AerodromeFlightType, AerodromeType, YesNo


class Aerodrome(BasePoint):
    """
    Aerodrome has following attrs:
        name: Aerodrome name in plain language (from base_model)
        type: Is it a heliport or airport, etc
        ifr_vfr: Accepts ifr or vfr or both flight types
        aur: Is the aerodrome available on request when it is supposed to be closed
        nav_aids: All Navigation-Aids of the aerodrome
    """

    four_letters = models.CharField(
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
    )
    ifr_vfr = models.CharField(
        "IFR/VFR Flight Operation",
        max_length=7,
        choices=AerodromeFlightType.choices,
        default=AerodromeFlightType.IFR_VFR,
    )
    is_international = models.BooleanField(
        verbose_name="Is International", choices=YesNo, default=True
    )
    aur = models.BooleanField("Available Upon Request", choices=YesNo, default=True)
    nav_aids = models.ManyToManyField(
        "points.NavAid", related_name="aerodromes", blank=True
    )

    class Meta(BasePoint.Meta):
        verbose_name = "Aerodrome"
        verbose_name_plural = "Aerodromes"
        indexes = [models.Index(fields=["name", "four_letters"])]

    def __str__(self):
        return f"{self.four_letters} - {self.name}"
