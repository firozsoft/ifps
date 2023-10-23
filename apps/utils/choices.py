from django.db import models

# from psycopg2.extras import NumericRange

YesNo = [(True, "Yes"), (False, "No")]


class AerodromeFlightType(models.TextChoices):
    IFR = "ifr", "IFR"
    VFR = "vfr", "VFR"
    IFR_VFR = "ifr_vfr", "IFR/VFR"


class AerodromeType(models.TextChoices):
    AIRPORT = "airport", "Airport"
    HELIPORT = "heliport", "Heliport"


class Direction(models.TextChoices):
    TO = "to", "TO"
    FROM = "from", "FROM"
    TO_FROM = "to_from", "TO/FROM"


class NavAidType(models.TextChoices):
    VOR = "vor", "VOR"
    NDB = "ndb", "NDB"
    DME = "dme", "DME"
    ILS = "ils", "ILS"
    DVOR = "dvor", "DVOR"
    TACAN = "tacan", "TACAN"
    NDB_DME = "ndb_dme", "NDB/DME"
    VOR_DME = "vor_dme", "VOR/DME"
    DVOR_DME = "dvor_dme", "DVOR/DME"
    VOR_TAC = "vor_tac", "VOR/TAC"


class NavAidUseCase(models.TextChoices):
    IN_ROUTE = "in_route"
    IN_AIRPORT = "in_airport"
    BOTH = "both"


class NotamType(models.TextChoices):
    NEW = "new"
    CANCELING = "canceling"
    REPLACEMENT = "replacement"


class RouteSchemeFlightNature(models.TextChoices):
    LANDING = "landing"
    DEPARTURE = "departure"
    DOMESTIC = "domestic"
    TRANSITION = "transition"
    OTHER = "other"


class SidStarType(models.TextChoices):
    SID = "SID", "SID"
    STAR = "STAR", "STAR"
    SID_STAR = "SID_STAR", "SID/STAR"


# def LevelRange() -> NumericRange:
#     return NumericRange(0, 650)
