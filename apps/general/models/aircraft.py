from django.db import models

from apps.general.models.abstracts import BaseModel


class Aircraft(BaseModel):
    type = models.CharField("Aircraft Type", max_length=50)

    class Meta:
        ordering = ('type',)
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"

    def __str__(self) -> str:
        return f'{self.type}'
