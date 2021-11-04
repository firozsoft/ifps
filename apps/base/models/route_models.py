from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.validators import RangeMaxValueValidator, RangeMinValueValidator
from django.db import models

from apps.base.models.abstract_models import BaseModel, BaseRoute
from apps.base.utils.choices import Direction, LevelRange, RouteSchemeFlightNature, SidStarType, YesNo
from apps.base.utils.validators import rs_dest_list, rs_flight_path, sid_star_name_validator


class Route(BaseRoute):
    class Meta(BaseRoute.Meta):
        pass

    # @property
    # def points(self):
    #     return list(set(
    #         point
    #         for section in self.sections.all
    #         for point in (section.point1, section.point2)))


class SidStar(BaseRoute):
    name = models.CharField("Name", max_length=7, unique=True, validators=[sid_star_name_validator, ])
    name_pl = models.CharField("Name PL", max_length=50, null=True, blank=True,
                               help_text='SID/STAR name in plain language')
    nav_aid = models.ForeignKey("base.NavAid", verbose_name="NAV-Aid", related_name="sid_star", on_delete=models.CASCADE)
    aerodromes = models.ManyToManyField("base.Aerodrome", verbose_name="Aerodromes", related_name="sid_stars")
    point = models.ForeignKey("base.Point", verbose_name="Point", on_delete=models.CASCADE)
    type = models.CharField(max_length=8, choices=SidStarType.choices)

    class Meta(BaseRoute.Meta):
        pass


class RouteSection(BaseModel):
    route = models.ForeignKey('base.Route', related_name='sections', on_delete=models.CASCADE)
    point1 = models.ForeignKey('base.Point', on_delete=models.CASCADE,
                               verbose_name="First Point", related_name="route_sections1")
    point2 = models.ForeignKey('base.Point', on_delete=models.CASCADE,
                               verbose_name="Second Point", related_name="route_sections2")
    direction = models.CharField("Direction", max_length=7, choices=Direction.choices, default=Direction.TO_FROM)
    distance = models.FloatField("Distance(NM)", default=1)
    min_safe_level = models.PositiveSmallIntegerField("Minimum Safe Level(FL)", default=1)
    upper_limit = models.PositiveSmallIntegerField("Upper Limit(FL)", default=500)
    lower_limit = models.PositiveSmallIntegerField("Lower Limit(FL)", default=1)
    rnav_rnp = models.CharField("RNAV/RNP Type", max_length=50, null=True, blank=True)
    min_rnav_level = models.PositiveSmallIntegerField("Min RNAV Level", default=1)
    mag_track = models.PositiveSmallIntegerField("Magnetic Track", default=1)
    lateral_limit = models.PositiveSmallIntegerField("Lateral limit", default=1)
    track_coloration = models.BooleanField("Track Coloration", default=True)
    remark = models.TextField("Remarks", null=True, blank=True)

    class Meta:
        ordering = ('route',)
        indexes = [models.Index(fields=['route', 'point1', 'point2'])]
        constraints = [models.UniqueConstraint(fields=['route', 'point1', 'point2'], name='unique_route_sections'), ]

    def __str__(self) -> str:
        return f"{self.route} between {self.point1} and {self.point2}"


class RouteScheme(BaseModel):
    start = models.CharField("From", max_length=50, null=True, blank=True)
    end = models.CharField("To", max_length=50, null=True, blank=True)
    flight_path = models.TextField("Flight Path", validators=[rs_flight_path, ])
    dest = models.CharField("Destinations/Next FIRs", max_length=50, validators=[rs_dest_list, ],
                            help_text="Comma separated list of Aerodrome/FIRs 4-letters", null=True, blank=True)
    ac_type = models.ForeignKey("base.Aircraft", verbose_name="Aircraft Type",
                                on_delete=models.CASCADE, null=True, blank=True)
    flight_nature = models.CharField("Flight Nature", max_length=10, choices=RouteSchemeFlightNature.choices)
    approved_level_range = IntegerRangeField(verbose_name="Approved Levels Range", default=LevelRange,
                                             validators=[RangeMinValueValidator(0), RangeMaxValueValidator(650)],
                                             help_text=("A range in a canonical form that includes the lower bound "
                                                        "and excludes the upper bound."), )
    not_approved_levels = models.CharField(verbose_name="Not Approved Levels", null=True, blank=True, max_length=50,
                                           help_text="Comma separated list of flight levels.")
    obligatory = models.BooleanField("Obligatory", choices=YesNo, default=False)

    class Meta:
        ordering = ('start',)
        indexes = [models.Index(fields=['start', 'end', ])]

    def __str__(self) -> str:
        return f'{self.start} to {self.end}'
