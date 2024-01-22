from django.contrib import admin

from apps.general.admin import BasePointAdmin
from apps.points.models import Point


@admin.register(Point)
class PointAdmin(BasePointAdmin):
    search_fields = ("name",)
    list_display = ("name", "coordinate", "is_active")
    search_fields = ("name", "coordinate")
    # filter_horizontal = ("fir_boundaries",)
    autocomplete_fields = ("fir",)
    fields = (
        "name",
        "is_active",
        ("coordinate", "latitude", "longitude"),
        # "location",
        "fir",
        "is_fir_boundary",
        # "fir_boundaries",
    )
