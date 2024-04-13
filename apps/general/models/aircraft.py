from django.db import models

from apps.general.models.base import AbstractBaseModel
from core.utils import validators
from core.utils.choices import WeakturbulenceCategory


class Aircraft(AbstractBaseModel):
    type = models.CharField(
        max_length=4,
        validators=[validators.type_of_aircraft_validator],
    )
    model = models.CharField(max_length=250)
    variant = models.CharField(max_length=250)
    manufacturer = models.CharField(max_length=250)
    description = models.CharField(max_length=250)
    engine_type = models.CharField(max_length=250)
    engine_count = models.PositiveSmallIntegerField()
    weakturbulence_category = models.CharField(max_length=1, choices=WeakturbulenceCategory.choices)

    class Meta:
        ordering = ["type"]
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"
        indexes = [models.Index(fields=["type"])]

    def __str__(self) -> str:
        return f"{self.type} - {self.model} - {self.manufacturer}"
