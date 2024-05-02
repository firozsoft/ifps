from django.db import models

from apps.general.models.base import BaseModel
from core.utils.choices import SidStarType, YesNo
from core.utils.validators import sid_star_name_validator


class SidStar(BaseModel):
    indicator = models.CharField(max_length=7, validators=[sid_star_name_validator])
    aerodrome = models.ForeignKey("aerodromes.Aerodrome", on_delete=models.CASCADE, related_name="sid_stars")
    point = models.ForeignKey("points.Point", on_delete=models.CASCADE)
    navaid = models.ForeignKey(
        "points.NavAid",
        verbose_name="Navigation Aid",
        related_name="sid_star",
        on_delete=models.CASCADE,
        limit_choices_to={"usecase__in": ["in_airport", "both"]},
    )
    type = models.CharField(max_length=8, choices=SidStarType.choices)
    rnp_app = models.BooleanField(default=False, choices=YesNo)
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "SID/STAR"
        verbose_name_plural = "SID/STARs"
        ordering = ["indicator"]
        indexes = [models.Index(fields=["indicator"])]
        constraints = [
            models.UniqueConstraint(
                fields=["indicator", "navaid", "aerodrome"],
                name="unique_sid_star_name_nav_ad",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_type_display()} {self.indicator} {self.aerodrome}"
