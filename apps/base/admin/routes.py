from django.contrib import admin

from ..models.routes import Route, RouteScheme, RouteSection, SidStar


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    pass


@admin.register(RouteScheme)
class RouteSchemeAdmin(admin.ModelAdmin):
    pass


@admin.register(RouteSection)
class RouteSectionAdmin(admin.ModelAdmin):
    pass


@admin.register(SidStar)
class SidStarAdmin(admin.ModelAdmin):
    pass
