from django.core.validators import MaxValueValidator, MinValueValidator

# from django.contrib.postgres.fields import IntegerRangeField
# from django.contrib.postgres.validators import RangeMaxValueValidator as RngMXV
# from django.contrib.postgres.validators import RangeMinValueValidator as RngMinV
from django.db import models

from apps.general.models import BaseModel

# from apps.utils.choices import LevelRange
from apps.utils.choices import RouteSchemeFlightNature, YesNo
from apps.utils.validators import rs_dest_list, rs_flight_path


class RouteScheme(BaseModel):
    start = models.CharField("From", max_length=50, null=True, blank=True)
    end = models.CharField("To", max_length=50, null=True, blank=True)
    flight_path = models.TextField("Flight Path", validators=[rs_flight_path])
    dest = models.CharField(
        "Destinations/Next FIRs",
        max_length=50,
        validators=[rs_dest_list],
        null=True,
        help_text="Comma separated list of Aerodrome/FIRs 4-letters",
        blank=True,
    )
    ac_type = models.ForeignKey(
        "general.Aircraft", verbose_name="Aircraft Type", on_delete=models.CASCADE, null=True, blank=True
    )
    flight_nature = models.CharField("Flight Nature", max_length=10, choices=RouteSchemeFlightNature.choices)
    approved_levels_upper_limit = models.PositiveSmallIntegerField(
        "Approved Levels Upper Limit", validators=[MinValueValidator(0), MaxValueValidator(999)]
    )
    not_approved_levels = models.CharField(
        verbose_name="Not Approved Levels",
        null=True,
        blank=True,
        max_length=100,
        help_text="Comma separated list of flight levels(e.g: 010,120,310).",
    )
    obligatory = models.BooleanField("Obligatory", choices=YesNo, default=False)

    class Meta:
        ordering = ("start",)
        indexes = [models.Index(fields=["start", "end"])]
        verbose_name = "Route Scheme"
        verbose_name_plural = "Route Schemes"

    def __str__(self) -> str:
        return f"{self.start} to {self.end}"

    def save(self, *args, **kwargs):
        self.not_approved_levels = ",".join(
            map(str.strip(), self.not_approved_levels.replace("F", "").split(","))
        )
        return super().save(*args, **kwargs)
