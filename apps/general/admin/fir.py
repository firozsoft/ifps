from django.contrib import admin
from django.db import models
from django.forms import Textarea, TextInput

from apps.aerodromes.models import Aerodrome
from apps.general.models import FIR


class AerodromeInline(admin.TabularInline):
    model = Aerodrome
    extra = 1
    formfield_overrides = {
        models.CharField: {"widget": TextInput(attrs={"size": "10"})},
        models.TextField: {"widget": Textarea(attrs={"rows": 2})},
    }
    fields = [
        "indicator",
        "plain_language_name",
        "iatacode",
        "coordinate",
        # "location",
        "type",
        "ifr_vfr",
        "is_international",
        "is_active",
        "aur",
        "fir",
        "is_fir_boundary",
    ]
    classes = ["collapse"]


@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    search_fields = ("indicator",)
    # inlines = [AerodromeInline]
