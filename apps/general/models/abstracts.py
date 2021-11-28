from django.db import models

from apps.utils import YesNo
from apps.utils.validators import coordinate_validator


class BaseModel(models.Model):
    """Abstract Base Model"""
    created = models.DateTimeField("Created", auto_now_add=True)
    updated = models.DateTimeField("Updated", auto_now=True)
    is_active = models.BooleanField("Active", choices=YesNo, default=True)

    class Meta:
        abstract = True


class BasePoint(BaseModel):
    """Abstract Point Model"""
    name = models.CharField("Name", max_length=50)
    coordinates = models.CharField("Coordinates", max_length=15, blank=True, null=True,
                                   validators=[coordinate_validator, ])

    class Meta:
        abstract = True
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"