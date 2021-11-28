from django.contrib import admin

from apps.points.models import NavAid


@admin.register(NavAid)
class NavAidAdmin(admin.ModelAdmin):
    fields = (
        'name', 'name_pl', 'type', 'coordinates', 'use_case',
        'fir', 'is_fir_boundary', 'fir_boundaries', 'is_active'
        )
    list_display = ('name', 'name_pl', 'type', 'coordinates', 'use_case', 'is_active')
    search_fields = ('name', 'name_pl', 'type', 'coordinates')
    list_filter = ('type', 'use_case', 'is_active')
    filter_horizontal = ('fir_boundaries',)
    autocomplete_fields = ('fir', )
