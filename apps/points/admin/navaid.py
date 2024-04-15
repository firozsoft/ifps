from django.contrib import admin

from apps.general.admin import BasePointAdmin
from apps.points.admin.resources import NavAidResource
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
        "usecase",
        "fir",
        "is_fir_boundary",
    ]
    list_display = [
        "__str__",
        "indicator",
        "plain_language_name",
        "type",
        "coordinate",
        "usecase",
        "is_active",
    ]
    search_fields = ["indicator", "plain_language_name", "type", "coordinate"]
    list_filter = ["type", "usecase", "is_active"]
    autocomplete_fields = ["fir"]
    resource_classes = [NavAidResource]
