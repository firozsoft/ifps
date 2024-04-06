from django.contrib import admin

from apps.routes.models.route_section import RouteSection


@admin.register(RouteSection)
class RouteSectionAdmin(admin.ModelAdmin):
    list_display = ["__str__"]
    autocomplete_fields = ["route", "point1", "point2"]
