from django.core.exceptions import ValidationError
from django.db import models

from apps.general.models import BasePoint
from core.utils.validators import point_name_validator


class Point(BasePoint):
    indicator = models.CharField(
        max_length=5,
        validators=[point_name_validator],
    )

    class Meta(BasePoint.Meta):
        verbose_name = "Point"
        verbose_name_plural = "Points"
        ordering = ["indicator"]
        indexes = [models.Index(fields=["indicator"])]

    def __str__(self) -> str:
        return self.indicator

    def clean(self) -> None:
        super().clean()
        similar_points = Point.objects.filter(indicator=self.indicator).exclude(
            pk=self.pk
        )  # Exclude current instance if it's being updated

        # ignore navaids (they could have indicator douplication), hasattr checks existence of navaid specific attr
        if similar_points.exists() and any(
            [True for similar_point in similar_points if not hasattr(similar_point, "type")]
        ):
            raise ValidationError("At least a point with the same indicator already exists.")
