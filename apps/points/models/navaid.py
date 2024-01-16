from django.core.exceptions import ValidationError
from django.db import models

from apps.general.models import BasePoint
from apps.points.models.point import Point
from core.utils.choices import NavAidType, NavAidUseCase


class NavAid(Point):
    type = models.CharField(
        "Type",
        max_length=8,
        choices=NavAidType.choices,
    )
    use_case = models.CharField(
        "Use Case",
        max_length=20,
        choices=NavAidUseCase.choices,
    )

    class Meta(BasePoint.Meta):
        verbose_name = "NavAid"
        verbose_name_plural = "NavAids"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"

    def clean(self):
        super().clean()

        if len(self.name) > 3:
            raise ValidationError({"name": "NvaAid name must be 2 or 3 characters."}, code="max_length")

        similar_navaids = NavAid.objects.filter(
            name=self.name, type=self.type, use_case=self.use_case
        ).exclude(pk=self.pk)  # Exclude current instance if it's being updated

        if similar_navaids.exists():
            raise ValidationError("At least a NavAid with this name, type, and use case already exists.")
