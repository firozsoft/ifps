from django.db import models

from .base import BaseModel


class Aircraft(BaseModel):
    type = models.CharField("Aircraft Type", max_length=4, unique=True)

    class Meta:
        ordering = ("type",)
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"

    def __str__(self) -> str:
        return f"{self.type}"
