from django.contrib.gis import admin

from apps.routes.models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    readonly_fields = ("_points",)
    fields = ["name", "is_active", "_points", "lines"]
    modifiable = False
