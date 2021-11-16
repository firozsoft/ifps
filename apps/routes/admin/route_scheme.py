from django.contrib import admin

from apps.routes.models import RouteScheme


@admin.register(RouteScheme)
class RouteSchemeAdmin(admin.ModelAdmin):
    pass
