# from django.contrib.gis import admin
from django.contrib import admin

from apps.routes.models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    search_fields = ["indicator"]
    fields = [
        "indicator",
        "is_active",
    ]
