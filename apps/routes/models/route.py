import json

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .abstract import BaseRoute


@receiver(post_save, sender="routes.RouteSection", dispatch_uid="update_route_points")
def update_route(**kwargs):
    instance = kwargs.pop("instance")
    instance.route.update_points()


class Route(BaseRoute):
    _points = models.TextField(db_column='points', null=True, blank=True)

    class Meta(BaseRoute.Meta):
        pass

    def get_points(self) -> list[str]:
        """Returns a list of route point names"""
        return json.loads(self._points)

    def update_points(self) -> None:
        lst = self.sections.values_list("point1__name", "point2__name")
        final_length = len(lst)
        s2 = set(map(lambda x: x[2], lst))
        res = [item for item in lst if item[1] not in s2]
        lst.remove(res[-1])
        d = {item[0]: i for i, item in enumerate(lst)}
        while len(res) != final_length:
            res.append(lst[d.pop(res[-1][1])])
        r = []
        _ = [r.append(item) for tup in res for item in tup if item not in r]
        self._points = json.dumps(r)
        self.save(update_fields=["points"])
