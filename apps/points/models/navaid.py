from django.core.exceptions import ValidationError
from django.db import models

from apps.points.models.point import Point
from core.utils.choices import NavAidType, NavAidUseCase


class NavAid(Point):
    type = models.CharField(
        max_length=8,
        choices=NavAidType.choices,
        help_text=f"Choices: {', '.join(tp[1] for tp in NavAidType.choices)}",
    )
    usecase = models.CharField(
        max_length=20,
        choices=NavAidUseCase.choices,
        help_text=f"Choices: {', '.join(tp[1] for tp in NavAidUseCase.choices)}",
    )

    class Meta(Point.Meta):
        verbose_name = "NavAid"
        verbose_name_plural = "NavAids"
        ordering = ["indicator"]

    def __str__(self):
        return f"{self.indicator} - {self.get_type_display()} - {self.get_usecase_display()}"

    @property
    def unique_indicator(self):
        return str(self)

    def clean(self):
        super().clean()

        if len(self.indicator) > 3:
            raise ValidationError(
                {"indicator": "NvaAid indicator must be 2 or 3 characters."},
                code="navaid_name_invalid_length",
            )

        similar_navaids = NavAid.objects.filter(
            indicator=self.indicator,
            type=self.type,
            usecase=self.usecase,
        ).exclude(pk=self.pk)  # Exclude current instance if it's being updated

        if similar_navaids.exists():
            msg = "At least a NavAid with this indicator, type, and usecase already exists."
            raise ValidationError(
                msg,
                code="navaid_duplicate_name_type_usecase",
            )
