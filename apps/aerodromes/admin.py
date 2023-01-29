from django.contrib import admin

from apps.aerodromes.models import Aerodrome
from apps.general.admin.generics import BasePointAdmin


@admin.register(Aerodrome)
class AerodromeAdmin(BasePointAdmin):
    search_fields = (
        "name",
        "four_letters",
    )
    list_display = ("name", "four_letters")
    list_filter = ("is_active",)
    filter_horizontal = ("nav_aids",)
