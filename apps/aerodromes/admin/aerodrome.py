from django.contrib import admin

from apps.aerodromes.models import Aerodrome


@admin.register(Aerodrome)
class AerodromeAdmin(admin.ModelAdmin):
    pass
