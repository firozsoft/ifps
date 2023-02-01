from django.db import models

from apps.general.models.abstracts import BaseModel


class FIR(BaseModel):
    """Stores all ICAO FIRs"""

    four_letters = models.CharField("ICAO Four Letters", max_length=4, unique=True)

    class Meta:
        ordering = ("four_letters",)
        verbose_name = "FIR"
        verbose_name_plural = "FIRs"

    def __str__(self):
        return self.four_letters
