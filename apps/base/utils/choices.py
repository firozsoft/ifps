from django.db import models


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


class NavAidStatus(models.TextChoices):
    OK = True, 'Available'
    US = False, 'Unserviceable(U/S)'


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
    BOTH = "both"
    OTHER = "other"


class SidStarType(models.TextChoices):
    SID = 'sid', 'SID'
    STAR = 'star', 'STAR'
    SID_STAR = 'sid_star', 'SID/STAR'


class YesNo(models.TextChoices):
    YES = True, 'Yes'
    NO = False, 'No'
