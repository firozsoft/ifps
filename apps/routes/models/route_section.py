from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

# from django.contrib.gis.db import models
from django.db import models
from django.db.models import F

from apps.general.models.abstracts import BaseModel
from apps.utils.choices import Direction, YesNo


class FlightLevelField(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        if not "default" in kwargs:
            kwargs["default"] = 1
        super().__init__(*args, **kwargs)
        self.validators = [MaxValueValidator(999), MinValueValidator(1)]


class RouteSection(BaseModel):
    route = models.ForeignKey("routes.Route", related_name="sections", on_delete=models.CASCADE)
    point1 = models.ForeignKey(
        "points.Point", on_delete=models.CASCADE, verbose_name="First Point", related_name="route_sections1"
    )
    point2 = models.ForeignKey(
        "points.Point", on_delete=models.CASCADE, verbose_name="Second Point", related_name="route_sections2"
    )
    # line = models.LineStringField(null=True, blank=True)
    direction = models.CharField("Direction", max_length=7, choices=Direction.choices, default=Direction.TO_FROM)
    distance = models.DecimalField("Distance(NM)", default=1, decimal_places=3, max_digits=4)
    min_safe_level = FlightLevelField("Minimum Safe Level(FL)")
    upper_limit = FlightLevelField("Upper Limit(FL)", default=999)
    lower_limit = FlightLevelField("Lower Limit(FL)")
    rnav_rnp = models.CharField("RNAV/RNP Type", max_length=50, null=True, blank=True)
    min_rnav_level = FlightLevelField("Min RNAV Level")
    mag_track = models.DecimalField("Magnetic Track", decimal_places=3, max_digits=4)
    lateral_limit = models.PositiveSmallIntegerField("Lateral limit")
    track_coloration = models.BooleanField("Track Coloration", default=True, choices=YesNo)
    domestic_only = models.BooleanField("Domestic Flights Only", default=False, choices=YesNo)
    remark = models.TextField("Remarks", null=True, blank=True)

    class Meta:
        ordering = ("route",)
        indexes = [models.Index(fields=["route", "point1", "point2"])]
        constraints = [
            models.UniqueConstraint(fields=["route", "point1"], name="unique_route_and_point1"),
            models.UniqueConstraint(fields=["route", "point2"], name="unique_route_and_point2"),
        ]
        verbose_name = "Route Section"
        verbose_name_plural = "Route Sections"

    def __str__(self) -> str:
        return f"{self.route} between {self.point1} and {self.point2}"

    def has_related_object(self, fk_field):
        return hasattr(self, fk_field) and self.__getattribute__(fk_field) is not None

    def clean(self):
        if self.has_related_object("point1") and self.has_related_object("point2"):
            if RouteSection.objects.filter(F(point1=self.point1) | F(point2=self.point2)).exists():
                raise ValidationError(
                    message=(
                        "There is another route-section which has the same "
                        "first point or same second point for this route"
                    ),
                    code="unique_route_and_point1_or_point2_error",
                )
