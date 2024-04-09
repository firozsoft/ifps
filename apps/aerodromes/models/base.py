from django.core.exceptions import ValidationError
from django.db import models

from apps.general.models.base import AbstractBaseModel


class AerodromeProperties(AbstractBaseModel):
    aerodrome = models.ForeignKey(
        "aerodromes.Aerodrome",
        related_name="%(class)ss",
        related_query_name="%(class)ss",
        on_delete=models.CASCADE,
        db_index=True,
    )
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        abstract = True
        ordering = ("aerodrome", "start")
        constraints = [
            models.UniqueConstraint(
                name="unique_%(class)s",
                fields=["aerodrome", "start", "end"],
            ),
        ]

    def __str__(self):
        return f"{self.__class__._meta.verbose_name}: {self.aerodrome} - {self.start.strftime("%y%m%d %H%M")} - {self.end.strftime("%y%m%d %H%M")}"

    def clean(self):
        if self.start > self.end:
            raise ValidationError(
                message="Start datetime can not be greater than end datetime.",
                code="ad_restriction_start_greater_than_end",
            )
