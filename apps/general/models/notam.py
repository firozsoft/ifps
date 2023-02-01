from datetime import datetime

from django.db import models

from apps.general.models.abstracts import AbstractBaseModel
from apps.utils.choices import NotamType


class NotamManager(models.Manager):
    """Add active filter to objects"""

    def active(self, date: datetime):
        """All valid NOTAMs for a given date"""
        return super().get_queryset().filter(start_date__lte=date, end_date__gte=date)


class Notam(AbstractBaseModel):
    number = models.CharField("Number", max_length=50)
    qcode = models.CharField("Q Code", max_length=50)
    type = models.CharField(
        "Type",
        choices=NotamType.choices,
        default=NotamType.NEW,
        max_length=11,
    )
    relevant = models.ForeignKey(
        "self",
        verbose_name="Relevant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="In case of replacement/cancellation, the relevant 'NOTAM'",
    )
    aerodrome = models.ForeignKey(
        "aerodromes.Aerodrome",
        verbose_name="Aerodrome",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    start_date = models.DateTimeField("Start")
    end_date = models.DateTimeField("End", null=True, blank=True)
    content = models.TextField("Content")

    objects = NotamManager()

    def __str__(self) -> str:
        return f"{self.number}"

    class Meta:
        ordering = ("number",)
        indexes = [models.Index(fields=["number"])]
        verbose_name = "NOTAM"
        verbose_name_plural = "NOTAMs"
