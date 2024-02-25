from django.contrib import admin

from apps.general.admin import BasePointAdmin
from apps.points.models import NavAid


@admin.register(NavAid)
class NavAidAdmin(BasePointAdmin):
    fields = (
        "indicator",
        "plain_language_name",
        "type",
        "is_active",
        ("coordinate", "latitude", "longitude"),
        # "location",
        "use_case",
        "fir",
        "is_fir_boundary",
        # "fir_boundaries",
    )
    list_display = (
        "__str__",
        "indicator",
        "plain_language_name",
        "type",
        "coordinate",
        "use_case",
        "is_active",
    )
    search_fields = ("indicator", "plain_language_name", "type", "coordinate")
    list_filter = ("type", "use_case", "is_active")
    # filter_horizontal = ("fir_boundaries",)
    autocomplete_fields = ("fir",)
