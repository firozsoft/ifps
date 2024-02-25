from django.core.exceptions import ValidationError
from django.db import models

from core.utils.choices import AerodromeFlightType


class DailyOperationalHour(models.Model):
    """Operational Hours of an Aerodrome which is seperated for VFR or IFR flight"""

    aerodrome = models.ForeignKey(
        "aerodromes.Aerodrome",
        verbose_name="Aerodrome",
        related_name="%(class)ss",
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    vfr_start_time = models.TimeField("VFR Start Time", null=True, blank=True)
    vfr_end_time = models.TimeField("VFR End Time", null=True, blank=True)

    class Meta:
        ordering = ("aerodrome", "date")
        verbose_name = "Operational Hour"
        verbose_name_plural = "Operational Hours"
        constraints = [
            models.UniqueConstraint(
                name="unique_%(class)s",
                fields=["aerodrome", "date", "start_time", "end_time"],
            ),
        ]

    def clean(self):
        if self.start_time > self.end_time:
            raise ValidationError(
                message="Start time can not be greater than end time.",
                code="ad_restriction_start_greater_than_end",
            )

        if (
            self.aerodrome
            and self.aerodrome.ifr_vfr in (AerodromeFlightType.VFR, AerodromeFlightType.IFR_VFR)
            and not all([self.vfr_start_time, self.vfr_end_time])
        ):
            raise ValidationError(
                message=f"Aerodrome {self.aerodrome} is useable for VFR flights, VFR start and end times are mandatory.",
                code="ad_vfr_times_required",
            )
        if self.vfr_start_time > self.vfr_end_time:
            raise ValidationError(
                message="VFR start time can not be greater than VFR end time",
                code="ad_vfr_times_start_greater_than_end",
            )
        return super().clean()
