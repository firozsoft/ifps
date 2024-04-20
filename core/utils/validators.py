from django.core.validators import RegexValidator

from core.utils import patterns

aftn_address_validator = RegexValidator(
    regex=patterns.AFTN_ADDRESS,
    message="AFTN addresses must be 8 characters long and should not start with I, J, X, or Q.",
    code="invalid_aftn_address",
)

aftn_addresses_validator = RegexValidator(
    regex=r"^(?![IJXQ])[A-Z]{8}(\s(?![IJXQ])[A-Z]{8})*$",
    message=(
        "AFTN addresses must be a space-separated list of 8-character strings, with each address not "
        "starting with I, J, X, or Q."
    ),
    code="invalid_aftn_addresses",
)

aircraft_identification_validator = RegexValidator(
    regex=patterns.AIRCRAFT_IDENTIFICATION,
    message="Aircraft identification must be between 2 and 7 characters long.",
    code="invalid_aircraft_identification",
)

type_of_aircraft_validator = RegexValidator(
    regex=patterns.TYPE_OF_AIRCRAFT,
    message="Aircraft type does not conform to ICAO Aircraft Type Designators (Doc 8643).",
    code="invalid_type_of_aircraft",
)

equipments_and_capacities_validators = RegexValidator(
    regex=patterns.EQUIPMENTS_CAPACITIES,
    message="Equipment specification does not conform to ICAO Doc 4444.",
    code="invalid_equipments",
)

coordinate_validator = RegexValidator(
    regex=patterns.COORDINATE,
    message=(
        "Coordinate must be in either DM format (7 characters) or DMS format (11 characters). "
        "e.g. 46N078W or 4602N07805W."
    ),
    code="invalid_coordinate",
)

point_name_validator = RegexValidator(
    regex=patterns.POINT,
    message="ATS point name must consist of 2 to 5 alphabetical characters.",
    code="invalid_point_name",
)

route_name_validator = RegexValidator(
    regex=patterns.ROUTE,
    message="Route name must consist upto 3 alphabetical characters followed upto 3 numeric characters.",
    code="invalid_route_name",
)

sid_star_name_validator = RegexValidator(
    regex=patterns.SID_STAR,
    message=(
        "SID/STAR name must consist of 2 to 5 alphabetical characters followed by 1 digit and another "
        "alphabetical character."
    ),
    code="invalid_sid_star_name",
)

aerodrome_validator = RegexValidator(
    regex=patterns.AERODROME,
    message="Aerodrome indicator is not valid.",
    code="invalid_aerodrome_indicator",
)

speed_validator = RegexValidator(
    regex=patterns.SPEED,
    message="Speed is not in a valid format.",
    code="invalid_speed",
)

level_validator = RegexValidator(
    regex=patterns.LEVEL,
    message="Level is not in a valid format.",
    code="invalid_level",
)

teet_validator = RegexValidator(
    regex=r"\d\d\d\d",
    message="TEET must be a 4-digit number representing hours and minutes.",
    code="invalid_teet",
)

fir_validator = RegexValidator(
    regex=patterns.FIR,
    message="FIR indicator is not valid.",
    code="invalid_fir_indicator",
)

rs_dest_list = RegexValidator(
    regex=r"^(?![IJXQ])([A-Z]{4},? ?)+$",
    message="RouteScheme destinations must be a list of comma-separated ICAO 4-letter FIR names.",
    code="invalid_route_scheme_dest",
)

notam_number_validator = RegexValidator(
    regex=r"^[A-RU-Z]\d{4}/\d{2}\s(NOTAMN|((NOTAMR|NOTAMC)\s[A-RU-Z]\d{4}/\d{2}))$",
    message=(
        "Each NOTAM series begins with a letter, followed by a four-digit number, a stroke, and a "
        "two-digit year. Additionally, NOTAM number includes the NOTAM type (NOTAMN, NOTAMR, or NOTAMC). "
        "For the latter two types, the number of the relevant NOTAM is provided."
    ),
    code="invalid_notam_number",
)

notam_qcode_validator = RegexValidator(
    regex=(
        r"^(?![IJXQ])[A-Z]{4}/Q[A-Z]{4}/(I|V|(IV)|K)/(K|(BO)|(NBO)|M)/(A|(AE)|(AW)|E|W|K)/\d{3}/\d{3}/"
        r"(?P<coordinate>(([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W))\d{3}$"
    ),
    message="Please refer to Doc 8126 to learn about the format of NOTAM item Q.",
    code="invalid_notam_qcode",
)

notam_item_a_validator = RegexValidator(
    regex=r"^(?![IJXQ])[A-Z]{4}(\s(?![IJXQ])[A-Z]{4}){0,6}$",
    message="Item A of a NOTAM must be either an aerodrome indicator or up to seven FIR indicators.",
    code="invalid_notam_item_a",
)

notam_item_b_validator = RegexValidator(
    regex=r"^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])([01][0-9]|2[0-3])[0-5][0-9]$",
    message="Item B of a NOTAM must be a ten-digit datetime group (year, month, day, hours, minutes) in UTC.",
    code="invalid_notam_item_b",
)

notam_item_c_validator = RegexValidator(
    regex=r"^((\d{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])([01][0-9]|2[0-3])[0-5][0-9])(EST)?)|(PERM)$",
    message=(
        "Item C of a NOTAM must be a ten-digit datetime group (year, month, day, hours, minutes) in UTC. "
        "Or the approximate duration should be indicated by a datetime group followed, without blank space, "
        "by the abbreviation EST. "
        "Or if the information is of a permanent nature, then the abbreviation PERM is inserted instead of "
        "the ten-digit datetime group"
    ),
    code="invalid_notam_item_b",
)

notam_item_f_g_validator = RegexValidator(
    regex=r"^((?!000)\d{3,}(M|(FT))\s((AMSL)|(AGL)|(SFC)|(GND)))|(FL(?!000)\d{3})$",
)
