from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models

from core.utils.choices import NotamType

from .base import AbstractBaseModel


class NotamManager(models.Manager):
    """Add active filter to objects"""

    def active(self, date=datetime.today()):
        """All valid NOTAMs for a given date"""
        return super().get_queryset().filter(start_date__lte=date, end_date__gte=date, is_active=True)


class Notam(AbstractBaseModel):
    number = models.CharField(max_length=50, unique=True)
    q_code = models.CharField(max_length=50)
    type = models.CharField(choices=NotamType.choices, default=NotamType.NEW, max_length=11)
    relevant = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="The NOTAM to be Replaced/Cancelled.",
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    content = models.TextField()

    objects = NotamManager()

    class Meta:
        ordering = ("number",)
        indexes = [models.Index(fields=["number"])]
        verbose_name = "NOTAM"
        verbose_name_plural = "NOTAMs"

    def __str__(self) -> str:
        return self.number

    def clean(self):
        super().clean()
        if self.type != NotamType.NEW and not self.relevant:
            raise ValidationError({"relevant": "This field is required."})
