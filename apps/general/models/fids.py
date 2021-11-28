from django.db import models

from apps.general.models.abstracts import BaseModel


class Fids(BaseModel):
    call_sign = models.CharField("call_sign", max_length=50)
    ac_type = models.ForeignKey("general.Aircraft", verbose_name="Aircraft Type",
                                null=True, on_delete=models.SET_NULL)
    dep = models.CharField("Departure", max_length=50)
    dest = models.CharField("Destination", max_length=50)
    depart_time = models.DateTimeField("Depart time", null=True, blank=True)
    arrival = models.DateTimeField("Arrival", null=True, blank=True)

    def __str__(self):
        return f'{self.call_sign} - {self.ac_type}'

    class Meta:
        ordering = ('call_sign',)
        indexes = [models.Index(fields=['call_sign', 'ac_type', ])]
        verbose_name = 'FIDS'
        verbose_name_plural = 'FIDS'
