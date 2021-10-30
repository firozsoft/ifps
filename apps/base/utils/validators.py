from django.core.validators import RegexValidator

from . import regex_patterns

point_name_validator = RegexValidator(
    regex=regex_patterns.POINT,
    message="ATS-Point name must be 2 to 5 Alphabetical characters",
    code="invalid_point_name")

coordinate_validator = RegexValidator(
    regex=fr"({regex_patterns.COR_DEGREES})|({regex_patterns.COR_DEG_MINS})",
    message="Coordinate must be either in degrees only (7 characters) or degrees and minutes (11 characters)",
    code="invalid_coordinates")

route_name_validator = RegexValidator(
    regex=regex_patterns.ROUTE,
    message="Route name must be 1 to 3 Alphabetical plus 1 to 3 numeric characters",
    code="invalid_route_name")

sid_star_name_validator = RegexValidator(
    regex=regex_patterns.SID_STAR,
    message="SID/STAR name must be 2 to 5 Alphabetical characters plus 1 Digit followed by an Alphabetical character",
    code="invalid_sid_star_name")

rs_dest_list = RegexValidator(
    regex=r"\b[A-Z]{4},?\b",
    message="RouteScheme destinations/nex FIRs must be a list of comma separated ICAO 4-letters",
    code="invalid_route_scheme_dest")

rs_flight_path = RegexValidator(
    regex=regex_patterns.ROUTESCHEME_PATH,
    message="Route scheme flight path shall be a combination of points and routes (SID/STAR maybe included).",
    code="invalid_route_scheme_path")
