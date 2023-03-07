from django.db import models

from apps.utils.choices import YesNo
from apps.utils.helpers import dms2dd
from apps.utils.validators import coordinate_validator

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
    # location = models.PointField(
    #     blank=True,
    #     null=True,
    #     # editable=False,
    # )
    fir = models.ManyToManyField(
        "airspaces.FIR",
        verbose_name="Located/Boundary FIR(s)",
        related_name="%(class)ss",
        help_text="The location of FIR boundary points can be assumed in more than one FIR",
    )
    is_fir_boundary = models.BooleanField(
        "Is FIR Boundary", choices=YesNo, default=False
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """save the model."""
        self.latitude, self.longitude = dms2dd(self.coordinates)
        # self.location = GEOSGeometry(
        #     f"POINT({self.longitude} {self.latitude})",
        #     srid=4326,
        # )
        super().save(*args, **kwargs)
