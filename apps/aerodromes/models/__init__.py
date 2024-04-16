from auditlog.registry import auditlog

from .aerodrome import Aerodrome
from .curfew import Curfew
from .daily_opr import DailyOperationalHour
from .temp_closure import TemporaryClosure

auditlog.register(Aerodrome)
auditlog.register(Curfew)
auditlog.register(DailyOperationalHour)
auditlog.register(TemporaryClosure)
