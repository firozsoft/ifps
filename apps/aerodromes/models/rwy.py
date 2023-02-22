from django.db import models


class RWY(models.Model):
    number = models.CharField(max_length=3)
    aerodrome = models.ForeignKey("aerodromes.Aerodrome", on_delete=models.CASCADE)
    length = models.PositiveSmallIntegerField(null=True, blank=True)
    threshold = models.PositiveSmallIntegerField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
