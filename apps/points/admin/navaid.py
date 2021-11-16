from django.contrib import admin

from apps.points.models import NavAid


@admin.register(NavAid)
class NavAidAdmin(admin.ModelAdmin):
    fields = (
        'name', 'name_pl', 'type', 'coordinates', 'usecase',
        'fir', 'is_fir_boundary', 'fir_boundaries', 'is_active'
        )
