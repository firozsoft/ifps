from django.db import models
from psycopg2.extras import NumericRange

YesNo = [(True, "Yes"), (False, "No")]


class AerodromeFlightType(models.TextChoices):
    IFR = "ifr", "IFR"
    VFR = "vfr", "VFR"
    IFR_VFR = "ifr_vfr", "IFR/VFR"

    __empty__ = "Unknown"


class AerodromeType(models.TextChoices):
    AIRPORT = "airport", "Airport"
    HELIPORT = "heliport", "Heliport"

    __empty__ = "Unknown"


class Direction(models.TextChoices):
    TO = "to"
    FROM = "from"
    TO_FROM = "to_from", "TO/FROM"

    __empty__ = "Unknown"


class NavAidType(models.TextChoices):
    VOR = "vor"
    NDB = "ndb"
    DME = "dme"
    ILS = "ils"
    DVOR = "dvor"
    TACAN = "tacan"
    NDB_DME = "ndb_dme", "NDB/DME"
    VOR_DME = "vor_dme", "VOR/DME"
    DVOR_DME = "dvor_dme", "DVOR/DME"
    VOR_TAC = "vor_tac", "VOR/TAC"

    __empty__ = "Unknown"


class NavAidUseCase(models.TextChoices):
    IN_ROUTE = "in_route"
    IN_AIRPORT = "in_airport"
    BOTH = "both"

    __empty__ = "Unknown"


class NotamType(models.TextChoices):
    NEW = "new"
    CANCELING = "canceling"
    REPLACEMENT = "replacement"

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
