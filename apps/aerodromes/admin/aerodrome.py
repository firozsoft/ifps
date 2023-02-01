from django.contrib.gis import admin

from apps.aerodromes.models import Aerodrome
from apps.general.admin.generics import BasePointAdmin


@admin.register(Aerodrome)
class AerodromeAdmin(BasePointAdmin):
    search_fields = ("four_letters", "plain_language_name")
    list_display = ("four_letters", "plain_language_name")
    list_filter = ("is_active",)
    filter_horizontal = ("nav_aids",)
    autocomplete_fields = ("fir",)
    fields = [
        "four_letters",
        "plain_language_name",
        "iatacode",
        "coordinates",
        "latitude",
        "longitude",
        "location",
        "type",
        "ifr_vfr",
        "is_international",
        "is_active",
        "aur",
        "fir",
        "is_fir_boundary",
        "nav_aids",
    ]
