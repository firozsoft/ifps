from django.db import models

from apps.general.models.abstracts import BaseModel


class RCAG(BaseModel):
    name = models.CharField(max_length=3, unique=True)
    remarks = models.TextField(null=True, blank=True)
