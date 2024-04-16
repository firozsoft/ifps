from auditlog.registry import auditlog

from .base import Route
from .route_scheme import RouteScheme
from .route_section import RouteSection
from .sid_star import SidStar

auditlog.register(Route)
auditlog.register(RouteScheme)
auditlog.register(RouteSection)
auditlog.register(SidStar)
