from django.db import models
from psycopg2.extras import NumericRange

YesNo = [(True, "Yes"), (False, "No")]


class AerodromeFlightType(models.TextChoices):
    IFR = "ifr", "IFR"
    VFR = "vfr", "VFR"
    IFR_VFR = "ifr_vfr", "IFR/VFR"

    __empty__ = "Unknown"


class AerodromeType(models.TextChoices):
    AIRPORT = "airport"
    HELIPORT = "heliport"

    __empty__ = "Unknown"


class Direction(models.TextChoices):
    TO = "to"
    FROM = "from"
    TO_FROM = "to_from", "TO/FROM"

    __empty__ = "Unknown"


class NavAidType(models.TextChoices):
    VOR = "vor", "VOR"
    NDB = "ndb", "NDB"
    DME = "dme", "DME"
    ILS = "ils", "ILS"
    NDB_DME = "ndb_dme", "NDB/DME"
    VOR_DME = "vor_dme", "VOR/DME"
    DVOR = "dvor", "DVOR"
    DVOR_DME = "dvor_dme", "DVOR/DME"
    TACAN = "tacan", "TACAN"
    VOR_TAC = "vor_tac", "VOR/TAC"

    __empty__ = "Unknown"


class NavAidUseCase(models.TextChoices):
    IN_ROUTE = "in_route", "In Route"
    IN_AIRPORT = "in_airport", "In Airport"
    BOTH = "both", "In Route/Airport"

    __empty__ = "Unknown"


class NotamType(models.TextChoices):
    NEW = "new", "N"
    CANCELING = "canceling", "C"
    REPLACEMENT = "replacement", "R"

    __empty__ = "Unknown"


class RouteSchemeFlightNature(models.TextChoices):
    LANDING = "landing"
    DEPARTURE = "departure"
    DOMESTIC = "domestic"
    TRANSITION = "transition"
    OTHER = "other"

    __empty__ = "Unknown"


class SidStarType(models.TextChoices):
    SID = "SID", "SID"
    STAR = "STAR", "STAR"
    SID_STAR = "SID_STAR", "SID/STAR"

    __empty__ = "Unknown"


def LevelRange() -> NumericRange:
    return NumericRange(0, 650)
