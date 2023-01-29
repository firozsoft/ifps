from django.core.exceptions import ValidationError
from django.db import models

from .abstract import AerodromeProperties


class DailyOperationalHour(AerodromeProperties):
    """Operational Hours of an Aerodrome which is seperated for VFR or IFR flight"""

    vfr_start_time = models.TimeField("VFR Start Time", null=True, blank=True)
    vfr_end_time = models.TimeField("VFR End Time", null=True, blank=True)

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Operational Hour"
        verbose_name_plural = "Operational Hours"

    def clean(self):
        if not any(self.vfr_start_time, self.vfr_end_time):
            raise ValidationError(
                message="VFR start and end times are mandatory",
                code="ad_vfr_times_required",
            )
        if self.vfr_start_time > self.vfr_end_time:
            raise ValidationError(
                message="VFR start time can not be greater than VFR end time",
                code="ad_vfr_times_start_greater_than_end",
            )
        return super().clean()
