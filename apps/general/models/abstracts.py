from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry

from apps.utils.choices import YesNo
from apps.utils.helpers import dm2dd
from apps.utils.validators import coordinate_validator


class AbstractBaseModel(models.Model):
    """Abstract Base Model"""

    created = models.DateTimeField("Created", auto_now_add=True)
    updated = models.DateTimeField("Updated", auto_now=True)
    is_active = models.BooleanField("Active", choices=YesNo, default=True)

    class Meta:
        abstract = True


class BaseModel(models.Model):
    """Base Model"""

    name = models.CharField(max_length=50, null=True, blank=True)
    created = models.DateTimeField("Created", auto_now_add=True)
    updated = models.DateTimeField("Updated", auto_now=True)
    is_active = models.BooleanField("Active", choices=YesNo, default=True)

    class Meta:
        abstract = True


class BasePoint(BaseModel):
    """Base Point Model"""

    coordinates = models.CharField(
        validators=[coordinate_validator],
        max_length=15,
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        blank=True,
        null=True,
        editable=False,
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        blank=True,
        null=True,
        editable=False,
    )
    location = models.PointField(
        blank=True,
        null=True,
        editable=False,
    )

    class Meta:
        abstract = True
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name}"

    def save(self, *args, **kwargs):
        """save the model."""
        self.latitude, self.longitude = dm2dd(self.coordinates)
        self.location = GEOSGeometry(
            f"POINT({self.longitude} {self.latitude})",
            srid=4326,
        )
        super().save(*args, **kwargs)
