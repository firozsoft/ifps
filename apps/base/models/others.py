from django.db import models

from .abstract import BaseModel


class Aircraft(BaseModel):
    type = models.CharField("Aircraft Type", max_length=50)

    class Meta:
        ordering = ('type',)
        verbose_name = "Aircraft"
        verbose_name_plural = "Aircraft"

    def __str__(self) -> str:
        return f'{self.type}'


class FIDS(BaseModel):
    callsign = models.CharField("Callsign", max_length=50)
    ac_type = models.ForeignKey("base.Aircraft",
                                verbose_name="Aircraft Type",
                                null=True, on_delete=models.SET_NULL)
    dep = models.CharField("Departure", max_length=50)
    dest = models.CharField("Destination", max_length=50)
    depart_time = models.DateTimeField("Depart time", null=True, blank=True)
    arrival = models.DateTimeField("Arrival", null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.callsign} - {self.ac_type}'

    class Meta:
        ordering = ('callsign',)
        indexes = [models.Index(fields=['callsign', 'ac_type', ])]
        verbose_name = 'FIDS'
        verbose_name_plural = 'FIDS'


class FIR(BaseModel):
    name = models.CharField("Name", max_length=4)

    class Meta:
        ordering = ('name',)
        verbose_name = "FIR"
        verbose_name_plural = "FIRs"


class NotamManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def active(self, date):
        return super().get_queryset().filter(start_date__lte=date,
                                             end_date__gte=date)


class NOTAM(BaseModel):
    number = models.CharField("Number", max_length=50)
    aerodrome = models.CharField("Aerodrome", max_length=50)
    start_date = models.DateTimeField("Start")
    end_date = models.DateTimeField("End")
    content = models.TextField("Content")

    objects = NotamManager()

    def __str__(self) -> str:
        return f'{self.number}'

    class Meta:
        ordering = ('number',)
        indexes = [models.Index(fields=['number', ])]
        verbose_name = 'NOTAM'
        verbose_name_plural = 'NOTAMs'
