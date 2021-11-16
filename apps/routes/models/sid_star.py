from django.db import models

from .abstract import BaseRoute
from apps.utils.choices import SidStarType
from apps.utils.validators import sid_star_name_validator


class SidStar(BaseRoute):
    name = models.CharField("Name", max_length=7, unique=True, validators=[sid_star_name_validator, ])
    name_pl = models.CharField("Name PL", max_length=50, null=True, blank=True,
                               help_text='SID/STAR name in plain language')
    nav_aid = models.ForeignKey("points.NavAid", verbose_name="NAV-Aid", related_name="sid_star",
                                on_delete=models.CASCADE)
    aerodromes = models.ManyToManyField("aerodromes.Aerodrome", verbose_name="Aerodromes",
                                        related_name="sid_stars")
    point = models.ForeignKey("points.Point", verbose_name="Point", on_delete=models.CASCADE)
    type = models.CharField(max_length=8, choices=SidStarType.choices)

    class Meta(BaseRoute.Meta):
        verbose_name = "SID/STAR"
        verbose_name_plural = "SID/STARs"
