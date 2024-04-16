from auditlog.registry import auditlog

from .navaid import NavAid
from .point import Point

auditlog.register(Point)
auditlog.register(NavAid)
