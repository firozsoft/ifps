from django.contrib import admin

from apps.routes.models.route_scheme import RouteScheme


@admin.register(RouteScheme)
class RouteSchemeAdmin(admin.ModelAdmin):
    list_display = ["__str__"]
