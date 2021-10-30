from base.models.abstract import BasePoint
from base.utils import (AerodromeFlightType, AerodromeType, NavAidStatus,
                        NavAidType, NavAidUsecase, YesNo,)
from base.utils.validators import navaid_name_validator, point_name_validator
from django.db import models


class Point(BasePoint):
    name = models.CharField("Name", max_length=5, unique=True,
                            validators=[point_name_validator, ])
    fir = models.ForeignKey("logic.FIR", verbose_name="Located FIR",
                            on_delete=models.CASCADE, related_name="points",
                            null=True, blank=True)
    is_fir_boundary = models.BooleanField("Is FIR Boundary",
                                          choices=YesNo.choices,
                                          default=YesNo.NO)
    fir_boundaries = models.ManyToManyField(
        "self", limit_choices_to={'is_fir_boundary': True},
        verbose_name="Connected FIR Boundaries", null=True, blank=True,)

    class Meta(BasePoint.Meta):
        verbose_name = "Point"
        verbose_name_plural = "Points"


class NavAid(Point):
    name_pl = models.CharField("Name PL", max_length=50,
                               help_text='NAV-Aid name in plain language')
    type = models.CharField("Type", max_length=7,
                            choices=NavAidType.choices)
    usecase = models.CharField("Use Case", max_length=10,
                               choices=NavAidUsecase.choices)
    is_active = models.BooleanField("Status",
                                    choices=NavAidStatus.choices,
                                    default=NavAidStatus.OK)

    class Meta(Point.Meta):
        verbose_name = "NavAid"
        verbose_name_plural = "NavAids"
        constraints = [
            models.UniqueConstraint(fields=['name', 'usecase'],
                                    name='unique_navaid_name_for_usecase'),
        ]


class Aerodrome(BasePoint):
    four_letters = models.CharField("ICAO Four Letters",
                                    max_length=4, unique=True)
    iatacode = models.CharField("IATA Code", max_length=50,
                                null=True, blank=True)
    type = models.CharField("Aerodrome Type", max_length=8,
                            choices=AerodromeType.choices,
                            default=AerodromeType.AIRPORT)
    ifr_vfr = models.CharField("IFR/VFR Flight Operation", max_length=7,
                               choices=AerodromeFlightType.choices,
                               default=AerodromeFlightType.IFR_VFR)
    is_international = models.BooleanField(verbose_name="Is International",
                                           choices=YesNo.choices,
                                           default=YesNo.YES)
    navaids = models.ManyToManyField('logic.NavAid', related_name="aerodromes")
    aur = models.BooleanField("Available Upon Request", choices=YesNo.choices,
                              default=YesNo.YES)

    class Meta(BasePoint.Meta):
        verbose_name = "Aerodrome"
        verbose_name_plural = "Aerodromes"
