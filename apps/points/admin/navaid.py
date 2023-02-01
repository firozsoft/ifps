from django.contrib import admin

from apps.general.admin.generics import BasePointAdmin
from apps.points.models import NavAid


@admin.register(NavAid)
class NavAidAdmin(BasePointAdmin):
    fields = (
        "name",
        "plain_language_name",
        "type",
        "is_active",
        "coordinates",
        "latitude",
        "longitude",
        "location",
        "use_case",
        "fir",
        "is_fir_boundary",
        # "fir_boundaries",
    )
    list_display = (
        "name",
        "plain_language_name",
        "type",
        "coordinates",
        "use_case",
        "is_active",
    )
    search_fields = ("name", "plain_language_name", "type", "coordinates")
    list_filter = ("type", "use_case", "is_active")
    # filter_horizontal = ("fir_boundaries",)
    autocomplete_fields = ("fir",)
