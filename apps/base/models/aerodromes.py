from django.core.exceptions import ValidationError
from django.db import models

from ..utils.choices import AerodromeFlightType, AerodromeType, YesNo
from .abstract import BaseModel, BasePoint


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
                                           choices=YesNo,
                                           default=True)
    navaids = models.ManyToManyField('base.NavAid', related_name="aerodromes")
    aur = models.BooleanField("Available Upon Request", choices=YesNo,
                              default=True)

    class Meta(BasePoint.Meta):
        verbose_name = "Aerodrome"
        verbose_name_plural = "Aerodromes"
        indexes = [models.Index(fields=['name', 'four_letters'])]


class AerodromeProperties(BaseModel):
    aerodrome = models.ForeignKey("base.Aerodrome",
                                  verbose_name="Aerodrome",
                                  related_name="%(class)s",
                                  on_delete=models.CASCADE)
    date = models.DateField("Date")
    start_time = models.TimeField("Start Time")
    end_time = models.TimeField("End Time")

    class Meta:
        abstract = True
        ordering = ('aerodrome',)
        indexes = [models.Index(fields=['aerodrome', 'date'])]
        constraints = [
            models.UniqueConstraint(
                fields=['aerodrome', 'date',
                        'start_time', 'end_time'],
                name='unique_%(class)s'),
        ]


class TemporaryClosure(AerodromeProperties):

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Aerodrome Temporary Closure"
        verbose_name_plural = "Aerodrome Temporary Closures"


class DailyOperationalHour(AerodromeProperties):
    vfr_start_time = models.TimeField("VFR Start Time",
                                      null=True, blank=True)
    vfr_end_time = models.TimeField("VFR End Time",
                                    null=True, blank=True)

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Aerodrome Operational Hour"
        verbose_name_plural = "Aerodrome Operational Hours"

    def clean(self) -> None:
        if not any([all([self.start_time, self.end_time]),
                    all([self.vfr_start_time, self.vfr_end_time])]):
            raise ValidationError(
                message="At least for IFR or VFR set both start and end times",
                code="at_least_one_start_and_end_pair_required")
        return super().clean()


class Curfew(AerodromeProperties):
    emergency = models.BooleanField("Emergency",
                                    choices=YesNo,
                                    default=True)
    scramble = models.BooleanField("Scramble",
                                   choices=YesNo,
                                   default=True)
    sm_flight = models.BooleanField("SM Flight",
                                    choices=YesNo,
                                    default=True)
    hospital = models.BooleanField("Hospital",
                                   choices=YesNo,
                                   default=True)
    head = models.BooleanField("Head Flight",
                               choices=YesNo,
                               default=True)
    search_and_rescue = models.BooleanField("SAR(search and rescue)",
                                            choices=YesNo,
                                            default=True)
    fire_fighting = models.BooleanField("Fire-Fighting",
                                        choices=YesNo,
                                        default=True)
    hazardous_matterial_carrier = models.BooleanField("Hazardous Matterials",
                                                      choices=YesNo,
                                                      default=True)
    medical_evacuation = models.BooleanField("Medical Evacoation",
                                             choices=YesNo,
                                             default=True)
    delayed_sch_flight = models.BooleanField("Deleyed Schedule Flight",
                                             choices=YesNo,
                                             default=True)
    military_il76 = models.BooleanField("Military IL76",
                                        choices=YesNo,
                                        default=True)
    coordinatable = models.BooleanField("Coordinatable",
                                        choices=YesNo,
                                        default=True)

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Aerodrome Curfew"
        verbose_name_plural = "Aerodrome Curfews"
