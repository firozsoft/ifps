from auditlog.registry import auditlog

from .aircraft import Aircraft
from .base import FIR
from .fids import FIDSData
from .fpl import FlightPlan
from .notam import Notam

auditlog.register(Aircraft)
auditlog.register(FIR)
auditlog.register(FIDSData)
auditlog.register(FlightPlan)
auditlog.register(Notam)
