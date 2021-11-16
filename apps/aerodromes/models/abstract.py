from django.db import models

from apps.general.models.abstracts import BaseModel


class AerodromeProperties(BaseModel):
    aerodrome = models.ForeignKey("aerodromes.Aerodrome", verbose_name="Aerodrome", related_name="%(class)s",
                                  on_delete=models.CASCADE)
    date = models.DateField("Date")
    start_time = models.TimeField("Start Time")
    end_time = models.TimeField("End Time")

    class Meta:
        abstract = True
        ordering = ('aerodrome',)
        indexes = [models.Index(fields=['aerodrome', 'date'])]
        constraints = [models.UniqueConstraint(name='unique_%(class)s',
                                               fields=['aerodrome', 'date', 'start_time', 'end_time'],
                                               ), ]

    def __str__(self):
        return f"{self.aerodrome} - {self.date}"
