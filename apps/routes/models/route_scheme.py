from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.general.models import BaseModel
from core.utils.choices import RouteSchemeFlightNature, YesNo
from core.utils.validators import rs_dest_list


class RouteScheme(BaseModel):
    start = models.CharField("Start", max_length=50, null=True, blank=True)
    end = models.CharField("End", max_length=50, null=True, blank=True)
    flight_path = models.TextField("Flight Path")
    dest = models.CharField(
        "Destination(s) or Next FIR(s)",
        max_length=50,
        validators=[rs_dest_list],
        help_text="Comma separated list of Aerodrome(s)/FIR(s) 4-letters",
        null=True,
        blank=True,
    )
    ac_type = models.ForeignKey(
        "general.Aircraft", verbose_name="Aircraft Type", on_delete=models.CASCADE, null=True, blank=True
    )
    flight_nature = models.CharField("Flight Nature", max_length=10, choices=RouteSchemeFlightNature.choices)
    approved_levels = models.PositiveSmallIntegerField(
        "Approved Levels", validators=[MinValueValidator(0), MaxValueValidator(999)]
    )
    not_approved_levels = models.CharField(
        verbose_name="Not Approved Levels",
        max_length=100,
        null=True,
        blank=True,
        help_text="Comma separated list of flight levels(e.g: 010, 120, 310).",
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
        if self.not_approved_levels:
            self.not_approved_levels = ",".join(
                map(str.strip, self.not_approved_levels.replace("F", "").split(","))
            )
        return super().save(*args, **kwargs)
