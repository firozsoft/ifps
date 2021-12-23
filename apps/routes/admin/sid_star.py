from django.contrib import admin

from apps.routes.models import SidStar


@admin.register(SidStar)
class SidStarAdmin(admin.ModelAdmin):
    search_fields = ('name', 'name_pl', 'aerodrome')
    list_display = ('name', 'name_pl', 'nav_aid', 'type', 'is_active')
    list_editable = ('is_active', )
    list_filter = ('nav_aid__type', 'type', 'is_active')
