# from django.contrib.gis.db import models

from .abstract import BaseRoute


class Route(BaseRoute):
    class Meta(BaseRoute.Meta):
        pass
