from django.contrib import admin

from apps.general.admin import BasePointAdmin
from apps.points.models.navaid import NavAid


@admin.register(NavAid)
class NavAidAdmin(BasePointAdmin):
    fields = [
        "indicator",
        "plain_language_name",
        "type",
        "is_active",
        ("coordinate", "latitude", "longitude"),
        # "location",
        "use_case",
        "fir",
        "is_fir_boundary",
    ]
    list_display = [
        "__str__",
        "indicator",
        "plain_language_name",
        "type",
        "coordinate",
        "use_case",
        "is_active",
    ]
    search_fields = ["indicator", "plain_language_name", "type", "coordinate"]
    list_filter = ["type", "use_case", "is_active"]
    autocomplete_fields = ["fir"]
    autocomplete_fields = ("fir",)
