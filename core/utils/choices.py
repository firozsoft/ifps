from django.db import models

YesNo: list[tuple[bool, str]] = [(True, "Yes"), (False, "No")]


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
    IN_ROUTE = "in_route", "In Route"
    IN_AIRPORT = "in_airport", "In Airport"
    BOTH = "both", "Both Route & Airport"


class NotamType(models.TextChoices):
    NEW = "new", "New"
    CANCELING = "canceling", "Canceling"
    REPLACEMENT = "replacement", "Replacement"


class RouteSchemeFlightNature(models.TextChoices):
    LANDING = "landing", "Landing"
    DEPARTURE = "departure", "Departure"
    DOMESTIC = "domestic", "Domestic"
    TRANSITION = "transition", "Transition"
    OTHER = "other", "Other"


class LevelUnit(models.TextChoices):
    A = "A", "A"
    F = "F", "F"
    S = "S", "S"
    VFR = "VFR", "VFR"


class SidStarType(models.TextChoices):
    SID = "SID", "SID"
    STAR = "STAR", "STAR"
    SID_STAR = "SID_STAR", "SID/STAR"


class FlightRules(models.TextChoices):
    IFR = "I", "I"
    VFR = "V", "V"
    IFR_VFR = "Y", "Y"
    VFR_IFR = "Z", "Z"


class FlightType(models.TextChoices):
    SCHEDULED_AIR_SERVICE = "S", "S"
    ON_SCHEDULED_AIR_TRANSPORT_OPERATION = "N", "N"
    GENERAL_AVIATION = "G", "G"
    MILITARY = "M", "M"
    OTHER = "X", "X"


class WeakturbulenceCategory(models.TextChoices):
    LIGHT = "L", "L"
    MEDIUM = "M", "M"
    HEAVY = "H", "H"
    SUPER_HEAVY = "J", "J"


# def LevelRange() -> NumericRange:
#     return NumericRange(0, 650)
