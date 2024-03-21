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
        help_text=f"Choices: {', '.join(tp[1] for tp in NavAidType.choices)}",
    )
    use_case = models.CharField(
        "Use Case",
        max_length=20,
        choices=NavAidUseCase.choices,
        help_text=f"Choices: {', '.join(tp[1] for tp in NavAidUseCase.choices)}",
    )

    class Meta(BasePoint.Meta):
        verbose_name = "Nav. Aid"
        verbose_name_plural = "Nav. Aids"
        ordering = ["indicator"]

    def __str__(self):
        return f"{self.indicator} - {self.get_type_display()} - {self.get_use_case_display()}"

    def clean(self):
        super().clean()

        if len(self.indicator) > 3:
            raise ValidationError(
                {"indicator": "NvaAid indicator must be 2 or 3 characters."},
                code="navaid_name_invalid_length",
            )

        similar_navaids = NavAid.objects.filter(
            indicator=self.indicator, type=self.type, use_case=self.use_case
        ).exclude(pk=self.pk)  # Exclude current instance if it's being updated

        if similar_navaids.exists():
            raise ValidationError(
                "At least a NavAid with this indicator, type, and usecase already exists.",
                code="navaid_duplicate_name_type_usecase",
            )
