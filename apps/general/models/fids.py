from django.db import models

from .base import AbstractBaseModel


class FIDSData(AbstractBaseModel):
    """To store FIDS data related to a callsign."""

    aircraft_identification = models.CharField(max_length=50)
    type_of_aircraft = models.ForeignKey(
        "general.Aircraft",
        null=True,
        on_delete=models.SET_NULL,
    )
    departure = models.CharField(max_length=50)
    destination = models.CharField(max_length=50)
    departure_time = models.DateTimeField(null=True, blank=True)
    arrival = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.aircraft_identification} - {self.type_of_aircraft}"

    class Meta:
        ordering = ["aircraft_identification"]
        indexes = [models.Index(fields=["aircraft_identification", "type_of_aircraft"])]
        verbose_name = "FIDS Data"
        verbose_name_plural = "FIDS Data"
