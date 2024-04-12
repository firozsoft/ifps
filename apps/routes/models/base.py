from django.db import models

from apps.general.models.base import BaseModel
from core.utils.validators import route_name_validator


class BaseRoute(BaseModel):
    """Abstract Route Model"""

    indicator = models.CharField(
        max_length=6,
        unique=True,
        validators=[route_name_validator],
    )

    class Meta:
        abstract = True
        ordering = ["indicator"]
        indexes = [models.Index(fields=["indicator"])]

    def __str__(self) -> str:
        return self.indicator


class Route(BaseRoute):
    class Meta(BaseRoute.Meta):
        verbose_name = "Route"
        verbose_name_plural = "Routes"
