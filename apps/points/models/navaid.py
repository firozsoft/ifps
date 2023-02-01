from django.core.validators import MinLengthValidator
from django.db import models

from apps.general.models.abstracts import BasePoint
from apps.utils import NavAidType, NavAidUseCase
from apps.utils.validators import point_name_validator


class NavAid(BasePoint):
    name = models.CharField(
        "Name",
        max_length=3,
        validators=[point_name_validator, MinLengthValidator(2)],
    )
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
        constraints = [
            models.UniqueConstraint(
                name="unique_name_type_use_case",
                fields=["name", "type", "use_case"],
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_type_display()}"
