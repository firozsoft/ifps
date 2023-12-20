# from django.contrib.gis import admin
from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput

from apps.aerodromes.models import (
    Aerodrome,
    Curfew,
    DailyOperationalHour,
    TemporaryClosure,
)
from apps.general.admin.generics import BasePointAdmin


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
    search_fields = ("indicator", "plain_language_name")
    list_display = ("indicator", "plain_language_name")
    list_filter = ("is_active",)
    autocomplete_fields = ("fir",)
    fields = [
        "indicator",
        "plain_language_name",
        "iatacode",
        ("coordinates", "latitude", "longitude"),
        # "location",
        "type",
        "ifr_vfr",
        "is_international",
        "is_active",
        "aur",
        "fir",
        "is_fir_boundary",
    ]

    inlines = [CurfewInline, TemporaryClosureInline, DailyOperationalHourInline]
