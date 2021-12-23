from django.core.exceptions import ValidationError
from django.db import models

from apps.points.models import Point
from apps.utils import NavAidType, NavAidUseCase


class NavAid(Point):
    name_pl = models.CharField("Name PL", max_length=50, null=True, blank=True,
                               help_text='Nav. Aid name in plain language')
    type = models.CharField("Type", max_length=8, choices=NavAidType.choices)
    use_case = models.CharField("Use Case", max_length=10,
                                choices=NavAidUseCase.choices)

    class Meta(Point.Meta):
        verbose_name = "NavAid"
        verbose_name_plural = "NavAids"
        constraints = [
            models.UniqueConstraint(
                name='unique_name_type_use_case',
                fields=['point_ptr_id', 'type', 'use_case'],),
        ]

    def clean(self) -> None:
        if len(self.name) not in {2, 3}:
            raise ValidationError(
                message="NAV-Aid name must be 2 or 3 Alphabetical characters",
                code="incorrect_nav_aid_name")
        return super().clean()

    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"
