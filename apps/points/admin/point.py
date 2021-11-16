from django.contrib import admin

from apps.points.models import Point


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    pass
