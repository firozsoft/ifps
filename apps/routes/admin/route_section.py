from django.contrib import admin

from apps.routes.models import RouteSection


@admin.register(RouteSection)
class RouteSectionAdmin(admin.ModelAdmin):
    autocomplete_fields = ["route", "point1", "point2"]
