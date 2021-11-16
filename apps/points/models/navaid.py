from django.core.exceptions import ValidationError
from django.db import models

from apps.points.models import Point
from apps.utils import NavAidType, NavAidUsecase


class NavAid(Point):
    name_pl = models.CharField("Name PL", max_length=50, null=True, blank=True,
                               help_text='NAV-Aid name in plain language')
    type = models.CharField("Type", max_length=7, choices=NavAidType.choices)
    use_case = models.CharField("Use Case", max_length=10, choices=NavAidUsecase.choices)

    class Meta(Point.Meta):
        verbose_name = "NavAid"
        verbose_name_plural = "NavAids"

    def clean(self) -> None:
        if len(self.name) not in {2, 3}:
            raise ValidationError(
                message="NAV-Aid name must be 2 or 3 Alphabetical characters",
                code="incorrect_navaid_name")
        return super().clean()
