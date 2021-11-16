from django.db import models

from apps.general.models.abstracts import BaseModel


class NotamManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def active(self, date):
        return super().get_queryset().filter(start_date__lte=date, end_date__gte=date)


class Notam(BaseModel):
    number = models.CharField("Number", max_length=50)
    aerodrome = models.CharField("Aerodrome", max_length=50, null=True, blank=True)
    start_date = models.DateTimeField("Start")
    end_date = models.DateTimeField("End")
    content = models.TextField("Content")

    objects = NotamManager()

    def __str__(self) -> str:
        return f'{self.number}'

    class Meta:
        ordering = ("number",)
        indexes = [models.Index(fields=["number", ])]
        verbose_name = "NOTAM"
        verbose_name_plural = "NOTAMs"
