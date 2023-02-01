from django.db import models

from apps.general.models.abstracts import BasePoint
from apps.utils.validators import point_name_validator


class Point(BasePoint):
    name = models.CharField(
        "Name",
        max_length=5,
        validators=[point_name_validator],
    )

    class Meta(BasePoint.Meta):
        verbose_name = "Point"
        verbose_name_plural = "Points"
        ordering = ("name",)
        indexes = [models.Index(fields=["name"])]

    def __str__(self) -> str:
        return f"{self.name}"
