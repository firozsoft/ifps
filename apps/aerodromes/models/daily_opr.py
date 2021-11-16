from django.core.exceptions import ValidationError
from django.db import models

from .abstract import AerodromeProperties


class DailyOperationalHour(AerodromeProperties):
    vfr_start_time = models.TimeField("VFR Start Time", null=True, blank=True)
    vfr_end_time = models.TimeField("VFR End Time", null=True, blank=True)

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Operational Hour"
        verbose_name_plural = "Operational Hours"

    def clean(self) -> None:
        if not any([all([self.start_time, self.end_time]),
                    all([self.vfr_start_time, self.vfr_end_time])]):
            raise ValidationError(
                message="At least for IFR or VFR set both start and end times",
                code="at_least_one_start_and_end_pair_required")
        return super().clean()
