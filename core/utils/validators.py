from django.core.validators import RegexValidator

from . import regex_patterns

aftn_address_validator = RegexValidator(
    regex=regex_patterns.AFTN_ADDRESS,
    message="AFTN addresses must be 8 characters long and should not start with I, J, X, or Q.",
    code="invalid_aftn_address",
)

aftn_addresses_validator = RegexValidator(
    regex="(" + regex_patterns.AFTN_ADDRESS + r"\s?)+",
    message="AFTN addresses must be a space-separated list of 8-character strings, with each address not starting with I, J, X, or Q.",
    code="invalid_aftn_addresses",
)

aircraft_identification_validator = RegexValidator(
    regex=regex_patterns.AIRCRAFT_IDENTIFICATION,
    message="Aircraft identification must be between 2 and 7 characters long.",
    code="invalid_aircraft_identification",
)

type_of_aircraft_validator = RegexValidator(
    regex=regex_patterns.TYPE_OF_AIRCRAFT,
    message="Aircraft type does not conform to ICAO Aircraft Type Designators (Doc 8643).",
    code="invalid_type_of_aircraft",
)

equipments_validators = RegexValidator(
    regex=regex_patterns.EQUIPMENTS_CAPACITIES,
    message="Equipment specification does not conform to ICAO Doc 4444.",
    code="invalid_equipments",
)

coordinate_validator = RegexValidator(
    regex=rf"({regex_patterns.COR_DEGREES})|({regex_patterns.COR_DEG_MINS})",
    message="Coordinate must be in either DM format (7 characters) or DMS format (11 characters), e.g., 46N078W or 4602N07805W.",
    code="invalid_coordinate",
)

point_name_validator = RegexValidator(
    regex=regex_patterns.POINT,
    message="ATS point name must consist of 2 to 5 alphabetical characters.",
    code="invalid_point_name",
)

route_name_validator = RegexValidator(
    regex=regex_patterns.ROUTE,
    message="Route name must consist of 1 to 3 alphabetical characters followed by 1 to 3 numeric characters.",
    code="invalid_route_name",
)

sid_star_name_validator = RegexValidator(
    regex=regex_patterns.SID_STAR,
    message="SID/STAR name must consist of 2 to 5 alphabetical characters followed by 1 digit and another alphabetical character.",
    code="invalid_sid_star_name",
)

aerodrome_validator = RegexValidator(
    regex=regex_patterns.AERODROME,
    message="Aerodrome indicator is not valid.",
    code="invalid_aerodrome_indicator",
)

speed_validator = RegexValidator(
    regex=regex_patterns.SPEED,
    message="Speed is not in a valid format.",
    code="invalid_speed",
)

level_validator = RegexValidator(
    regex=regex_patterns.LEVEL,
    message="Level is not in a valid format.",
    code="invalid_level",
)

teet_validator = RegexValidator(
    regex=r"(?P<teet>\d\d\d\d)",
    message="TEET must be a 4-digit number representing hours and minutes.",
    code="invalid_teet",
)

fir_validator = RegexValidator(
    regex=regex_patterns.AERODROME,
    message="FIR indicator is not valid.",
    code="invalid_fir_indicator",
)

rs_dest_list = RegexValidator(
    regex=r"^(?![IJXQ])([A-Z]{4},? ?)+$",
    message="RouteScheme destinations must be a list of comma-separated ICAO 4-letter FIR names.",
    code="invalid_route_scheme_dest",
)
