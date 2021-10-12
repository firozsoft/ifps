from django.core.validators import RegexValidator

point_name_validator = RegexValidator(
    regex=r"\b([A-Z]{2,5})(?<!DCT|IFR|VFR)\b",
    message="ATS-Point name must be 2 to 5 Alphabetical characters",
    code="invalid_point_name")

navid_name_validator = RegexValidator(
    regex=r"\b([A-Z]{2,3})(?<!DCT|IFR|VFR)\b",
    message="NAV-Aid name must be 2 or 3 Alphabetical characters",
    code="invalid_navaid_name")

coordinate_validator = RegexValidator(
    regex=r"\b([0-8]\d|90)(N|S)(0[\d]{2}|1[0-7]\d|180)(E|W)|([0-8]\d|90)[0-5]\d(N|S)(0[\d]{2}|1[0-7]\d|180)[0-5]\d(E|W)\b",
    message="Coordinate must be either in degrees only (7 characters) or degrees and minutes (11 characters)",
    code="invalid_coordinates")

route_name_validator = RegexValidator(
    regex=r"\b[A-Z]{1,3}[\d]{1,3}\b",
    message="Route name must be 1 to 3 Alphabetical plus 1 to 3 numeric characters",
    code="invalid_route_name")

sid_star_name_validator = RegexValidator(
    regex=r"\b[A-Z]{2,5}[1-9][A-Z]\b",
    message="SID/STAR name must be 2 to 5 Alphabetical characters plus 1 Digit followed by an Alphabetical character",
    code="invalid_route_name")
