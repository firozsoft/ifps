from django.contrib import admin

from apps.general.admin import BasePointAdmin
from apps.points.models import Point


@admin.register(Point)
class PointAdmin(BasePointAdmin):
    search_fields = ("indicator",)
    list_display = ("indicator", "coordinate", "is_active")
    search_fields = ("indicator", "coordinate")
    # filter_horizontal = ("fir_boundaries",)
    autocomplete_fields = ("fir",)
    fields = (
        "indicator",
        "is_active",
        ("coordinate", "latitude", "longitude"),
        # "location",
        "fir",
        "is_fir_boundary",
        # "fir_boundaries",
    )
