from django.core.validators import RegexValidator

from . import regex_patterns
type_of_aircraft_validator = RegexValidator(
    regex=regex_patterns.TYPE_OF_AIRCRAFT,
    message="Ac. type doesn't fit as specified in Doc 8643 ICAO pulications Aircraft Type Designators.",
    code="invalid_type_of_aircraft",
)

coordinate_validator = RegexValidator(
    regex=rf"({regex_patterns.COR_DEGREES})|({regex_patterns.COR_DEG_MINS})",
    message="Coordinate must be either in DM(7 characters) or DMS(11 characters). e.g: 46N078W, 4602N07805W",
    code="invalid_coordinate",
)

point_name_validator = RegexValidator(
    regex=regex_patterns.POINT,
    message="ATS-Point name must be 2 to 5 Alphabetical characters",
    code="invalid_point_name",
)

route_name_validator = RegexValidator(
    regex=regex_patterns.ROUTE,
    message="Route name must be 1 to 3 Alphabetical plus 1 to 3 numeric characters",
    code="invalid_route_name",
)

sid_star_name_validator = RegexValidator(
    regex=regex_patterns.SID_STAR,
    message="SID/STAR name must be 2 to 5 Alphabetical characters plus 1 Digit followed by an Alphabetical character",
    code="invalid_sid_star_name",
)

aerodrome_validator = RegexValidator(
    regex=regex_patterns.AERODROME,
    message="",
    code="invalid_aerodrome_indicator",
)

fir_validator = RegexValidator(
    regex=regex_patterns.AERODROME,
    message="",
    code="invalid_fir_indicator",
)

rs_dest_list = RegexValidator(
    regex=r"^(?![IJXQ])([A-Z]{4},? ?)+$",
    message="RouteScheme destination/next FIRs must be a list of comma separated ICAO 4-letters FIR names",
    code="invalid_route_scheme_dest",
)
