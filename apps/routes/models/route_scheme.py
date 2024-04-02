from django.db import models

from apps.general.models import BaseModel
from core.utils.choices import RouteSchemeFlightNature, YesNo
from core.utils.validators import rs_dest_list


class RouteScheme(BaseModel):
    start = models.CharField("Start", max_length=50)
    end = models.CharField("End", max_length=50)
    flight_path = models.TextField("Flight Path")
    dest = models.CharField(
        "Destination(s) or Next FIR(s)",
        max_length=50,
        validators=[rs_dest_list],
        help_text="Comma separated list of Aerodrome(s)/FIR(s) 4-letters",
        null=True,
        blank=True,
    )
    type_of_aircraft = models.ForeignKey(
        "general.Aircraft",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    flight_nature = models.CharField(
        max_length=10,
        choices=RouteSchemeFlightNature.choices,
        help_text=f"Choices: {', '.join(tp[1] for tp in RouteSchemeFlightNature.choices)}",
    )
    approved_levels = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        help_text="Comma separated list of flight levels(e.g: 010, 120, 310).",
    )
    not_approved_levels = models.CharField(
        max_length=250,
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
