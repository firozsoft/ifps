from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db.models import F

from apps.general.models.abstracts import BaseModel
from apps.utils import Direction


class RouteSection(BaseModel):
    route = models.ForeignKey(
        "routes.Route", related_name="sections", on_delete=models.CASCADE
    )
    point1 = models.ForeignKey(
        "points.Point",
        on_delete=models.CASCADE,
        verbose_name="First Point",
        related_name="route_sections1",
    )
    point2 = models.ForeignKey(
        "points.Point",
        on_delete=models.CASCADE,
        verbose_name="Second Point",
        related_name="route_sections2",
    )
    line = models.LineStringField(null=True, blank=True)
    direction = models.CharField(
        "Direction", max_length=7, choices=Direction.choices, default=Direction.TO_FROM
    )
    distance = models.FloatField("Distance(NM)", default=1)
    min_safe_level = models.PositiveSmallIntegerField(
        "Minimum Safe Level(FL)", default=1
    )
    upper_limit = models.PositiveSmallIntegerField("Upper Limit(FL)", default=500)
    lower_limit = models.PositiveSmallIntegerField("Lower Limit(FL)", default=1)
    rnav_rnp = models.CharField("RNAV/RNP Type", max_length=50, null=True, blank=True)
    min_rnav_level = models.PositiveSmallIntegerField("Min RNAV Level", default=1)
    mag_track = models.PositiveSmallIntegerField("Magnetic Track", default=1)
    lateral_limit = models.PositiveSmallIntegerField("Lateral limit", default=1)
    track_coloration = models.BooleanField("Track Coloration", default=True)
    remark = models.TextField("Remarks", null=True, blank=True)

    class Meta:
        ordering = ("route",)
        indexes = [models.Index(fields=["route", "point1", "point2"])]
        constraints = [
            models.UniqueConstraint(
                fields=["route", "point1"], name="unique_route_and_point1"
            ),
            models.UniqueConstraint(
                fields=["route", "point2"], name="unique_route_and_point2"
            ),
        ]
        verbose_name = "Route Section"
        verbose_name_plural = "Route Sections"

    def __str__(self) -> str:
        return f"{self.route} between {self.point1} and {self.point2}"

    def clean(self):
        if RouteSection.objects.filter(
            F(point1=self.point1) | F(point2=self.point2)
        ).exists():
            raise ValidationError(
                message=(
                    "There is another route-section which has the same "
                    "first point or same second point for this route"
                ),
                code="unique_route_and_point1_or_point2_error",
            )
