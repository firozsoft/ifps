from django.db import models

from apps.utils.choices import SidStarType, YesNo
from apps.utils.validators import sid_star_name_validator

from .abstract import BaseRoute


class SidStar(BaseRoute):
    name = models.CharField(
        "Name",
        max_length=7,
        validators=[
            sid_star_name_validator,
        ],
    )
    name_pl = models.CharField(
        "Name PL",
        max_length=50,
        null=True,
        blank=True,
        help_text="SID/STAR name in plain language",
    )
    nav_aid = models.ForeignKey(
        "points.NavAid",
        verbose_name="Nav. Aid",
        related_name="sid_star",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    rnp_app = models.BooleanField(default=False, choices=YesNo)
    aerodrome = models.ForeignKey(
        "aerodromes.Aerodrome",
        verbose_name="Aerodrome",
        on_delete=models.CASCADE,
        related_name="sid_stars",
    )
    point = models.ForeignKey(
        "points.Point", verbose_name="Point", on_delete=models.CASCADE
    )
    type = models.CharField(max_length=8, choices=SidStarType.choices)
    rwy = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name="RunWay(s)",
        help_text="Slash separated list of runways",
    )

    class Meta(BaseRoute.Meta):
        verbose_name = "SID/STAR"
        verbose_name_plural = "SID/STARs"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "nav_aid", "aerodrome"],
                name="unique_sid_star_name_nav_ad",
            ),
        ]
