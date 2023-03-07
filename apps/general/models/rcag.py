from django.db import models

from apps.general.models.abstracts import BasePoint


class RCAG(BasePoint):
    name = models.CharField(max_length=3, unique=True)
    remarks = models.TextField(null=True, blank=True)
