from django.contrib import admin

from apps.general.admin.generics import BasePointAdmin
from apps.points.models import NavAid


@admin.register(NavAid)
class NavAidAdmin(BasePointAdmin):
    fields = (
        "name",
        "name_pl",
        "type",
        "is_active",
        "coordinates",
        "latitude",
        "longitude",
        "location",
        "use_case",
        "fir",
        "is_fir_boundary",
        "fir_boundaries",
    )
    list_display = ("name", "name_pl", "type", "coordinates", "use_case", "is_active")
    search_fields = ("name", "name_pl", "type", "coordinates")
    list_filter = ("type", "use_case", "is_active")
    filter_horizontal = ("fir_boundaries",)
    autocomplete_fields = ("fir",)
