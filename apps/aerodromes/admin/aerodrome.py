# from django.contrib.gis import admin
from django.contrib import admin

from apps.aerodromes.models.aerodrome import Aerodrome
from apps.aerodromes.models.curfew import Curfew
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.aerodromes.models.temp_closure import TemporaryClosure
from apps.general.admin import BasePointAdmin


class CurfewInline(admin.TabularInline):
    model = Curfew
    extra = 1
    classes = ["collapse"]


class DailyOperationalHourInline(admin.TabularInline):
    model = DailyOperationalHour
    extra = 1
    classes = ["collapse"]


class TemporaryClosureInline(admin.TabularInline):
    model = TemporaryClosure
    extra = 1
    classes = ["collapse"]


@admin.register(Aerodrome)
class AerodromeAdmin(BasePointAdmin):
    search_fields = ["indicator", "plain_language_name"]
    list_display = ["indicator", "plain_language_name"]
    list_filter = ["is_active"]
    autocomplete_fields = ["fir"]
    fields = [
        "indicator",
        "plain_language_name",
        "iatacode",
        ("coordinate", "latitude", "longitude"),
        # "location",
        "fir",
        "type",
        "ifr_vfr",
        "is_international",
        "aur",
        "is_fir_boundary",
        "is_active",
    ]

    inlines = [CurfewInline, TemporaryClosureInline, DailyOperationalHourInline]
