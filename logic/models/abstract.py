from django.db import models
from logic.utils import YesNo
from logic.utils.validators import coordinate_validator, route_name_validator


class BaseModel(models.Model):
    """Abstract BaseModel"""
    created = models.DateTimeField("Created", auto_now_add=True)
    updated = models.DateTimeField("Updated", auto_now=True)
    is_active = models.BooleanField("Is Active", choices=YesNo.choices,
                                    default=YesNo.YES)

    class Meta:
        abstract = True


class BasePoint(BaseModel):
    """Abstract Point Model"""
    name = models.CharField("Name", max_length=50)
    coordinates = models.CharField("Coordinates", max_length=11,
                                   blank=True, null=True,
                                   validators=[coordinate_validator, ])

    class Meta:
        abstract = True
        ordering = ('name',)
        indexes = [models.Index(fields=['name', ])]

    def __str__(self):
        return f'{self.name}'


class BaseRoute(BaseModel):
    """Abstract Route Model"""
    name = models.CharField("Name", max_length=6, unique=True,
                            validators=[route_name_validator, ])

    class Meta:
        abstract = True
        ordering = ('name',)
        indexes = [models.Index(fields=['name', ])]

    def __str__(self):
        return f'{self.name}'
