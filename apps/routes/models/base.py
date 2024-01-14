from django.db import models

from apps.general.models import BaseModel
from core.utils.validators import route_name_validator


class BaseRoute(BaseModel):
    """Abstract Route Model"""

    name = models.CharField(
        "Name",
        max_length=6,
        unique=True,
        validators=[route_name_validator],
    )

    class Meta:
        abstract = True
        ordering = ("name",)
        indexes = [models.Index(fields=["name"])]

    def __str__(self) -> str:
        return f"{self.name}"


class Route(BaseRoute):
    def get_points(self):
        return set(point for tp in self.sections.values_list("point1", "point2") for point in tp)

    class Meta(BaseRoute.Meta):
        pass
