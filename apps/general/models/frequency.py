from django.db import models

from apps.general.models.abstracts import AbstractBaseModel


class Frequency(AbstractBaseModel):
    frequency = models.DecimalField(max_digits=6, decimal_places=3, unique=True)
    rcags = models.ManyToManyField("general.RCAG")

    def __str__(self):
        return f"{self.frequency}"
