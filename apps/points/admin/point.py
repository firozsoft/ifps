from django.contrib import admin

from apps.general.admin import BasePointAdmin
from apps.points.admin.resources import PointResource
from apps.points.models.point import Point


@admin.register(Point)
class PointAdmin(BasePointAdmin):
    list_display = ["indicator", "coordinate", "is_active"]
    search_fields = ["indicator", "coordinate"]
    fields = [
        "indicator",
        "is_active",
        ("coordinate", "latitude", "longitude"),
        # "location",
        "fir",
        "is_fir_boundary",
    ]
    autocomplete_fields = ["fir"]
    resource_classes = [PointResource]
