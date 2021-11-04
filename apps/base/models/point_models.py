from django.core.exceptions import ValidationError
from django.db import models

from ..utils.choices import NavAidType, NavAidUsecase, YesNo
from ..utils.validators import point_name_validator
from .abstract_models import BasePoint


class Point(BasePoint):
    name = models.CharField("Name", max_length=5,
                            validators=[point_name_validator, ])
    fir = models.ForeignKey("base.FIR", verbose_name="Located FIR",
                            on_delete=models.CASCADE, related_name="%(class)s",
                            null=True, blank=True)
    is_fir_boundary = models.BooleanField("Is FIR Boundary",
                                          choices=YesNo,
                                          default=False)
    fir_boundaries = models.ManyToManyField(
        "self", related_name="connected_points", blank=True,
        limit_choices_to={'is_fir_boundary': True},
        verbose_name="Connected FIR Boundaries")

    class Meta(BasePoint.Meta):
        verbose_name = "Point"
        verbose_name_plural = "Points"
        indexes = [models.Index(fields=['name', ])]

    def is_on_route(self, route):
        return route in self.route_section1.values_list(
            'route', flat=True) or route in self.route_section2.values_list(
            'route', flat=True)


class NavAid(Point):
    name_pl = models.CharField("Name PL", max_length=50, null=True, blank=True,
                               help_text='NAV-Aid name in plain language')
    type = models.CharField("Type", max_length=7,
                            choices=NavAidType.choices)
    usecase = models.CharField("Use Case", max_length=10,
                               choices=NavAidUsecase.choices)

    class Meta(Point.Meta):
        verbose_name = "NavAid"
        verbose_name_plural = "NavAids"

    def clean(self) -> None:
        if len(self.name) not in {2, 3}:
            raise ValidationError(
                message="NAV-Aid name must be 2 or 3 Alphabetical characters",
                code="incorrect_navaid_name")
        return super().clean()
