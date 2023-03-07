# from django.contrib.gis.db import models
from django.db import models

from apps.general.models.abstracts import BaseModel


class AbstractBaseAirspace(BaseModel):
    name = models.CharField(max_length=50, unique=True, null=True, blank=True)
    # shape = models.PolygonField()
    upper_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    lower_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    fir = models.ForeignKey(
        "airspaces.FIR", related_name="%(class)ss", on_delete=models.CASCADE
    )

    class Meta:
        abstract = True


class BaseAirspaces(AbstractBaseAirspace):
    frequencies = models.ManyToManyField("general.Frequency")

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name


class Sector(BaseAirspaces):
    pass


class TMA(BaseAirspaces):
    aerodromes = models.ManyToManyField("aerodromes.Aerodrome")


class CTR(BaseAirspaces):
    aerodrome = models.ManyToManyField("aerodromes.Aerodrome")


class CTA(BaseAirspaces):
    pass


class ProhibitedArea(AbstractBaseAirspace):
    pass


class DangerArea(AbstractBaseAirspace):
    pass


class CautionArea(AbstractBaseAirspace):
    pass


class RestrictedArea(AbstractBaseAirspace):
    pass


class AerialRefueling(AbstractBaseAirspace):
    pass


class FIR(BaseModel):
    four_letters = models.CharField("ICAO Four Letters", max_length=4, unique=True)
    # shape = models.PolygonField(null=True, blank=True)

    class Meta:
        ordering = ("four_letters",)
        verbose_name = "FIR"
        verbose_name_plural = "FIRs"

    def __str__(self):
        return self.four_letters


class ACC(BaseModel):
    four_letters = models.CharField("ICAO Four Letters", max_length=4, unique=True)
    # shape = models.MultiPolygonField(null=True, blank=True)
    sectors = models.ManyToManyField("airspaces.Sector")

    class Meta:
        ordering = ("four_letters",)
        verbose_name = "ACC"
        verbose_name_plural = "ACCs"

    def __str__(self):
        return self.four_letters
