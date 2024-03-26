from django.db import models

from core.utils.choices import YesNo
from core.utils.helpers import dms2dd
from core.utils.validators import coordinate_validator, fir_validator

# from django.contrib.gis.geos import GEOSGeometry


class AbstractBaseModel(models.Model):
    """Abstract Base Model"""

    created = models.DateTimeField("Created", auto_now_add=True)
    updated = models.DateTimeField("Updated", auto_now=True)
    is_active = models.BooleanField("Active", choices=YesNo, default=True)

    class Meta:
        abstract = True


class BaseModel(AbstractBaseModel):
    """Base Model"""

    plain_language_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True


class FIR(BaseModel):
    indicator = models.CharField(
        "ICAO Four Letters",
        max_length=4,
        unique=True,
        validators=[fir_validator],
    )
    # shape = models.PolygonField(null=True, blank=True)

    class Meta:
        verbose_name = "FIR"
        verbose_name_plural = "FIRs"
        ordering = ["indicator"]
        indexes = [models.Index(fields=["indicator"])]

    def __str__(self):
        return self.indicator


class BasePoint(BaseModel):
    """Base Point Model"""

    coordinate = models.CharField(
        validators=[coordinate_validator],
        max_length=15,
        unique=True,
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
    # location = models.PointField(
    #     blank=True,
    #     null=True,
    #     # editable=False,
    # )
    fir = models.ManyToManyField(
        to=FIR,
        verbose_name="FIR(s)",
        related_name="%(class)ss",
        help_text="FIR boundary points must have 2 FIRs",
    )
    is_fir_boundary = models.BooleanField("Is FIR Boundary", choices=YesNo, default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """save the model."""
        self.latitude, self.longitude = dms2dd(self.coordinate)
        # self.location = GEOSGeometry(
        #     f"POINT({self.longitude} {self.latitude})",
        #     srid=4326,
        # )
        super().save(*args, **kwargs)
