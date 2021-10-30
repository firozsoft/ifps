from django.db import models
from psycopg2.extras import NumericRange


class AerodromeFlightType(models.TextChoices):
    IFR = 'ifr', 'IFR'
    VFR = 'vfr', 'VFR'
    IFR_VFR = 'ifr_vfr', 'IFR/VFR'


class AerodromeType(models.TextChoices):
    AIRPORT = 'airport'
    HELIPORT = 'heliport'


class Direction(models.TextChoices):
    TO = 'to'
    FROM = 'from'
    TO_FROM = 'to_from', 'TO/FROM'


class NavAidType(models.TextChoices):
    VOR = "vor", "VOR"
    NDB = "ndb", "NDB"
    DME = "dme", "DME"
    ILS = "ils", "ILS"
    NDB_DME = "ndb_dme", "NDB/DME"
    VOR_DME = "vor_dme", "VOR/DME"
    DVOR = "dvor", "DVOR"
    TACAN = "tacan", "TACAN"
    VOR_TAC = "vor_tac", "VOR/TAC"


class NavAidUsecase(models.TextChoices):
    IN_ROUTE = "in_route", "In Route"
    IN_AIRPORT = "in_airport", "In Airport"
    BOTH = "both", "Both"


class RouteSchemeFlightNature(models.TextChoices):
    LANDING = "landing"
    DEPARTURE = "departure"
    DOMESTIC = "domestic"
    TRANSITION = "transition"
    OTHER = "other"


class SidStarType(models.TextChoices):
    SID = 'sid', 'SID'
    STAR = 'star', 'STAR'
    SID_STAR = 'sid_star', 'SID/STAR'


def LevelRange() -> NumericRange:
    return NumericRange(0, 650)


YesNo = [(True, 'Yes'),
         (False, 'No')]
