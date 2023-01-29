import json

from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .abstract import BaseRoute


@receiver(post_save, sender="routes.RouteSection", dispatch_uid="update_route_points")
def update_route(**kwargs):
    instance = kwargs.pop("instance")
    instance.route.lines.append(instance.line)
    instance.route.update_points(instance.point1, instance.point2)


class Route(BaseRoute):
    _points = models.TextField(db_column="points", null=True, blank=True)
    lines = models.MultiLineStringField(null=True, blank=True)

    class Meta(BaseRoute.Meta):
        pass

    def get_points(self) -> list[str]:
        """Returns a list of route point names"""
        return json.loads(self._points)

    def update_points(self, point_1, point2) -> None:
        av_points = self._points.split(", ") if self._points else []
        if point_1.name not in av_points:
            av_points.append(point_1.name)
        if point2.name not in av_points:
            av_points.append(point2.name)
        self._points = ", ".join(av_points)
        self.save(update_fields=["_points"])
