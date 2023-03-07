from django.contrib import admin

from apps.general.admin.generics import BasePointAdmin
from apps.points.models import Point


@admin.register(Point)
class PointAdmin(BasePointAdmin):
    search_fields = ("name",)
    list_display = ("name", "coordinates", "is_active")
    search_fields = ("name", "coordinates")
    list_filter = ("is_active",)
    # filter_horizontal = ("fir_boundaries",)
    autocomplete_fields = ("fir",)
    fields = (
        "name",
        "is_active",
        ("coordinates",
        "latitude",
        "longitude"),
        # "location",
        "fir",
        "is_fir_boundary",
        # "fir_boundaries",
    )
