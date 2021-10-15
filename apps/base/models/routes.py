from base.models.abstract import BaseModel, BaseRoute
from base.utils.choices import Direction, RouteSchemeFlightNature
from base.utils.validators import sid_star_name_validator
from django.db import models


class Route(BaseRoute):
    pass
    # @property
    # def points(self):
    #     return set(
    #         point for section in self.sections for point in section.point1
    #     )


class SidStar(BaseRoute):
    name = models.CharField("Name", max_length=7, unique=True,
                            validators=[sid_star_name_validator, ])
    name_pl = models.CharField("Name PL", max_length=50, null=True, blank=True
                               help_text='SID/STAR name in plain language')
    navaid = models.ForeignKey("logic.NavAid", verbose_name="NAV-Aid",
                               on_delete=models.CASCADE)
    aerodromes = models.ManyToManyField("logic.Aerodrome",
                                        verbose_name="Aerodromes",
                                        related_name="sid_stars")
    point = models.ForeignKey("logic.Point", verbose_name="Point",
                              on_delete=models.CASCADE)


class RouteSectionsDetail(BaseModel):
    route = models.ForeignKey('logic.Route', related_name='sections',
                              on_delete=models.CASCADE)
    point1 = models.ForeignKey('logic.Point', on_delete=models.CASCADE,
                               verbose_name="First Point",
                               related_name="fpoint")
    point2 = models.ForeignKey('logic.Point', on_delete=models.CASCADE,
                               verbose_name="Second Point",
                               related_name="spoint")
    direction = models.CharField("Direction", max_length=7,
                                 choices=Direction.choices,
                                 default=Direction.TO_FROM)
    distance = models.FloatField("Distance(NM)", default=1)
    min_safe_level = models.PositiveSmallIntegerField(
        "Minimum Safe Level(FL)", default=1)
    upper_limit = models.PositiveSmallIntegerField(
        "Upper Limit(FL)", default=500)
    lower_limit = models.PositiveSmallIntegerField(
        "Lower Limit(FL)", default=1)
    rnav_rnp = models.CharField("RNAV/RNP Type", max_length=50,
                                null=True, blank=True)
    min_rnav_level = models.PositiveSmallIntegerField(
        "Min RNAV Level", default=1)
    mag_track = models.PositiveSmallIntegerField(
        "Magnetic Track", default=1)
    lateral_limit = models.PositiveSmallIntegerField(
        "Lateral limit", default=1)
    track_coloration = models.BooleanField("Track Coloration", default=True)
    remark = models.TextField("Remarks", null=True, blank=True)

    class Meta:
        ordering = ('route',)
        indexes = [models.Index(fields=['route', 'point1', 'point2'])]
        constraints = [
            models.UniqueConstraint(
                fields=['route', 'point1', 'point2'],
                name='unique_route_section'
            ),
        ]

    def __str__(self):
        return "{} between {} and {}".format(
            self.route, self.point1, self.point2)


class RouteScheme(BaseModel):
    start = models.CharField("From", max_length=500, null=True, blank=True)
    end = models.CharField("To", max_length=500, null=True, blank=True)
    flight_path = models.TextField("Flight Path")
    third_fir = models.ForeignKey("base.FIR", verbose_name="3rd FIR",
                                  on_delete=models.CASCADE,
                                  null=True, blank=True)
    ac_type = models.ForeignKey("base.Aircraft", verbose_name="Aircraft Type",
                                on_delete=models.CASCADE,
                                null=True, blank=True)
    flight_nature = models.CharField("Flight Nature", max_length=7,
                                     choices=RouteSchemeFlightNature.choices)
    approved_level_range = models.CharField("Approved Levels", max_length=550,
                                            null=True, blank=True)
    not_ap_level = models.CharField("NotApproved Levels", max_length=550,
                                    null=True, blank=True)
    obligatory = models.BooleanField("Obligatory", default=False)
