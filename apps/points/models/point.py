from django.db import models

from apps.general.models.abstracts import BasePoint
from apps.utils import YesNo
from apps.utils.validators import point_name_validator


class Point(BasePoint):
    name = models.CharField("Name", max_length=5, validators=[point_name_validator, ])
    fir = models.ForeignKey("general.FIR", verbose_name="Located FIR", null=True, blank=True,
                            on_delete=models.CASCADE, related_name="%(class)s")
    is_fir_boundary = models.BooleanField("Is FIR Boundary", choices=YesNo, default=False)
    fir_boundaries = models.ManyToManyField("self", related_name="connected_points", blank=True,
                                            limit_choices_to={'is_fir_boundary': True},
                                            verbose_name="Connected FIR Boundaries")

    class Meta(BasePoint.Meta):
        verbose_name = "Point"
        verbose_name_plural = "Points"
        indexes = [models.Index(fields=['name', ])]
