from django.core.exceptions import ValidationError
from django.db import models

from apps.general.models.base import AbstractBaseModel


class AerodromeProperties(AbstractBaseModel):
    aerodrome = models.ForeignKey(
        "aerodromes.Aerodrome",
        verbose_name="Aerodrome",
        related_name="%(class)ss",
        on_delete=models.CASCADE,
    )
    date = models.DateField("Date")
    start_time = models.TimeField("Start Time")
    end_time = models.TimeField("End Time")

    class Meta:
        abstract = True
        ordering = ("aerodrome", "date")
        indexes = [models.Index(fields=["aerodrome", "date"])]
        constraints = [
            models.UniqueConstraint(
                name="unique_%(class)s",
                fields=["aerodrome", "date", "start_time", "end_time"],
            ),
        ]

    def __str__(self):
        return f"{self.aerodrome} - {self.date}"

    def clean(self):
        if self.start_time > self.end_time:
            raise ValidationError(
                message="Start time can not be greater than End time",
                code="ad_times_start_greater_than_end",
            )
