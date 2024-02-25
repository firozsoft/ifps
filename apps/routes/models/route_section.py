from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

# from django.contrib.gis.db import models
from django.db import models
from django.db.models import Q

from apps.general.models import AbstractBaseModel
from core.utils.choices import Direction, YesNo


class FlightLevelField(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        if "default" not in kwargs:
            kwargs["default"] = 1
        super().__init__(*args, **kwargs)
        self.validators.extend([MinValueValidator(1), MaxValueValidator(999)])


class RouteSection(AbstractBaseModel):
    route = models.ForeignKey(
        "routes.Route",
        related_name="sections",
        on_delete=models.CASCADE,
    )
    point1 = models.ForeignKey(
        "points.Point",
        on_delete=models.CASCADE,
        verbose_name="First Point",
        related_name="route_sections_as_p1",
    )
    point2 = models.ForeignKey(
        "points.Point",
        on_delete=models.CASCADE,
        verbose_name="Second Point",
        related_name="route_sections_as_p2",
    )
    # line = models.LineStringField(null=True, blank=True)
    direction = models.CharField(
        "Direction",
        max_length=7,
        choices=Direction.choices,
        default=Direction.TO_FROM,
        help_text=(
            "Direction between first & second points (either `from` p1 toward p2 Or `to` p1 coming out of p2). "
            f"Choices: {', '.join(tp[1] for tp in Direction.choices)}"
        ),
    )
    distance = models.DecimalField("Distance(NM)", default=1, decimal_places=3, max_digits=4)
    minimum_safe_altitude = FlightLevelField(null=True, blank=True)
    minimum_safe_flight_level = FlightLevelField()
    lower_limit_altitude = FlightLevelField(null=True, blank=True)
    lower_limit_flight_level = FlightLevelField()
    upper_limit_altitude = FlightLevelField(default=999, null=True, blank=True)
    upper_limit_flight_level = FlightLevelField(default=999)
    minimum_rnav_flight_level = FlightLevelField(null=True, blank=True)
    rnav_rnp = models.CharField("RNAV/RNP Type", max_length=50, null=True, blank=True)
    mag_track = models.DecimalField("Magnetic Track", decimal_places=1, max_digits=4)
    lateral_limit = models.PositiveSmallIntegerField("Lateral limit (NM)")
    track_coloration = models.BooleanField("Track Correlation", default=True, choices=YesNo)
    domestic_only = models.BooleanField("Domestic Flights Only", default=False, choices=YesNo)
    not_for_over_flights = models.BooleanField("Not For OverFlights", default=False, choices=YesNo)
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

    def clean(self):
        if all((getattr(self, "point1"), getattr(self, "point2"))):
            if (
                RouteSection.objects.filter(
                    Q(route=self.route) & (Q(point1=self.point1) | Q(point2=self.point2))
                )
                .exclude(pk=self.pk)  # Exclude current instance if it's being updated
                .exists()
            ):
                raise ValidationError(
                    message=(
                        "There is another route-section which has the same "
                        "first point or same second point for this route"
                    ),
                    code="unique_route_and_point1_or_point2_error",
                )
