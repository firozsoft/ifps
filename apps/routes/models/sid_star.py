from django.db import models

from apps.general.models import BaseModel
from core.utils.choices import SidStarType, YesNo
from core.utils.validators import sid_star_name_validator


class SidStar(BaseModel):
    indicator = models.CharField("Indicator", max_length=7, validators=[sid_star_name_validator])
    plain_language_name = models.CharField("Plain Language Name", max_length=50, null=True, blank=True)
    aerodrome = models.ForeignKey("aerodromes.Aerodrome", on_delete=models.CASCADE, related_name="sid_stars")
    point = models.ForeignKey("points.Point", on_delete=models.CASCADE)
    nav_aid = models.ForeignKey(
        "points.NavAid",
        verbose_name="Nav.Aid",
        related_name="sid_star",
        on_delete=models.CASCADE,
    )
    type = models.CharField(max_length=8, choices=SidStarType.choices)
    rnp_app = models.BooleanField(default=False, choices=YesNo)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "SID/STAR"
        verbose_name_plural = "SID/STARs"
        ordering = ["indicator"]
        indexes = [models.Index(fields=["indicator"])]
        constraints = [
            models.UniqueConstraint(
                fields=["indicator", "nav_aid", "aerodrome"],
                name="unique_sid_star_name_nav_ad",
            ),
        ]
