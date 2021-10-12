from django.db import models
from logic.models.abstract import BaseModel, BaseRoute
from logic.utils.choices import Direction
from logic.utils.validators import sid_star_name_validator


class Route(BaseRoute):
    
    @property
    def points(self):
        return set(
            point for section in self.sections for point in section.point1
        )


class SidStar(BaseRoute):
    name = models.CharField("Name", max_length=7, unique=True,
                            validators=[sid_star_name_validator, ])
    name_pl = models.CharField("Name PL", max_length=50,
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


class RouteScheme(models.Model):
    start = models.CharField("Start", default='', max_length=4)
    end = models.CharField("End", default='', max_length=4,
                           null=True, blank=True)
    dest = models.CharField(
        "Destinations",
        default='',
        max_length=500,
        null=True,
        blank=True)
    nextfir = models.CharField(
        "Next FIR",
        default='',
        max_length=50,
        null=True,
        blank=True)
    ac_type = models.CharField(
        "Aircraft Type",
        default='',
        max_length=50,
        null=True,
        blank=True)
    intention = models.CharField(
        "Intention",
        choices=INTENTION_CHOICES,
        default='both',
        max_length=50)
    approved_level_range = models.CharField(
        "Approved Levels",
        default='', max_length=550, null=True, blank=True)
    not_ap_level = models.CharField(
        "NotApproved Levels",
        default='',
        max_length=550,
        null=True,
        blank=True)
    route = models.TextField("Routes")
    entry_point = models.ForeignKey(Point,
                                    verbose_name="Entry Point",
                                    related_name="route_scheme_entry",
                                    on_delete=models.CASCADE,
                                    null=True, blank=True,
                                    # limit_choices_to={'is_fir_boundary':True,
                                    # "is_active":True}
                                    )
    exit_point = models.ForeignKey(
        Point,
        verbose_name="Exit Point",
        related_name="route_scheme_exit",
        on_delete=models.CASCADE,
        null=True, blank=True,
        # limit_choices_to={'is_fir_boundary':True, "is_active":True}
    )
    obligatory = models.BooleanField("Obligatory", default=False)
    publish_date = models.DateTimeField("Publish Date", default=now)
    is_active = models.BooleanField("Is Active?", default=True)
    active_date = models.DateTimeField("Activation Date", default=now)

    def __str__(self):
        return '{} to {} via {}'.format(self.start, self.end, self.route)

    def get_absolute_route(self, part: tuple()):
        from . import RouteSections
        first = part[0]
        second = part[2]
        route = part[1]
        section_list1 = list()
        section_list2 = list()
        funded = False

        this_route_Sections = RouteSections.filter(route__name__iexact=route)

        if this_route_Sections.filter(first_point=first).exists():
            if this_route_Sections.filter(
                    first_point=first,
                    second_point=second).exists():
                section_list1.append((first, second))
                funded = True
            else:
                fpoint = this_route_Sections.get(first_point=first).first_point

                for i in range(0, len(this_route_Sections)):
                    if not this_route_Sections.filter(
                            first_point=fpoint).exists():
                        break
                    spoint = this_route_Sections.get(
                        first_point=fpoint).second_point
                    section_list1.append((fpoint, spoint))
                    fpoint = spoint
                    if this_route_Sections.filter(
                            first_point=spoint, second_point=second).exists():
                        section_list1.append((spoint, second))
                        funded = True
                        break

        if not funded and this_route_Sections.filter(
                first_point=second).exists():
            section_list1.clear()
            if this_route_Sections.filter(
                    first_point=second,
                    second_point=first).exists():
                section_list2.append((second, first))
                funded = True
            else:
                fpoint = this_route_Sections.get(
                    first_point=second).first_point
                for i in range(0, len(this_route_Sections)):
                    if not this_route_Sections.filter(
                            first_point=fpoint).exists():
                        break
                    spoint = this_route_Sections.get(
                        first_point=fpoint).second_point
                    section_list1.append((fpoint, spoint))
                    fpoint = spoint
                    if this_route_Sections.filter(
                            first_point=spoint, second_point=first).exists():
                        section_list1.append((spoint, first))
                        funded = True
                        break

        section_list = section_list1 or section_list2
        scheme = section_list[0][0] + route + section_list[-1][1]
        return scheme
