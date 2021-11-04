from django.contrib import admin

from ..models.point_models import NavAid, Point


@admin.register(NavAid)
class NavAidAdmin(admin.ModelAdmin):
    fields = (
        'name', 'name_pl', 'type', 'coordinates', 'usecase',
        'fir', 'is_fir_boundary', 'fir_boundaries', 'is_active'
    )


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    pass
