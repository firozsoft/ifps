from django.db import models

from apps.general.models.abstracts import BaseModel


class FIR(BaseModel):
    """Stores all ICAO FIRs"""

    name = models.CharField("Name", max_length=4)

    class Meta:
        ordering = ("name",)
        verbose_name = "FIR"
        verbose_name_plural = "FIRs"

    def __str__(self):
        return self.name
