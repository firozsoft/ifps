from base.models.abstract import BaseModel
from django.db import models


class FIR(BaseModel):
    name = models.CharField("Name", max_length=4)

    class Meta:
        verbose_name = "FIR"
        verbose_name_plural = "FIRs"


class Aircraft(BaseModel):
    type = models.CharField("Aircraft Type", max_length=50)

    class Meta:
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"

    def __str__(self):
        return f'{self.type}'
