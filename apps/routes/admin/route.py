# from django.contrib.gis import admin
from django.contrib import admin

from apps.routes.models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    fields = [
        "name",
        "is_active",
    ]
