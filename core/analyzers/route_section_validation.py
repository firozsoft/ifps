from apps.routes.models import RouteSection


def check_altitude(level, db_section: RouteSection, err):
    level = int(level.replace("A", ""))
    if db_section.minimum_safe_altitude and level < db_section.minimum_safe_altitude:
        err["logical_error"].append(
            "Invalid altitude. Minimun Safe Altitude for"
            f"route {db_section.route.indicator} - btw {db_section.point1.indicator} & {db_section.point2.indicator} is"
            f"{db_section.minimum_safe_altitude}."
        )
    if db_section.lower_limit_altitude and level < db_section.lower_limit_altitude:
        err["logical_error"].append(
            "Invalid altitude. Minimun Limit Altitude for"
            f"route {db_section.route.indicator} - btw {db_section.point1.indicator} & {db_section.point2.indicator} is"
            f"{db_section.lower_limit_altitude}."
        )
    if db_section.upper_limit_altitude and level > db_section.upper_limit_altitude:
        err["logical_error"].append(
            "Invalid altitude. Upper Limit Altitude for"
            f"route {db_section.route.indicator} - btw {db_section.point1.indicator} & {db_section.point2.indicator} is"
            f"{db_section.lower_limit_altitude}."
        )


def check_flight_level(level, db_section: RouteSection, err):
    level = int(level.replace("F", ""))
    if db_section.minimum_safe_flight_level and level < db_section.minimum_safe_flight_level:
        err["logical_error"].append(
            "Invalid flight level. Minimun Safe Flight Level for"
            f"route {db_section.route.indicator} - btw {db_section.point1.indicator} & {db_section.point2.indicator} is"
            f"{db_section.minimum_safe_flight_level}."
        )
    if db_section.lower_limit_flight_level and level < db_section.lower_limit_flight_level:
        err["logical_error"].append(
            "Invalid flight level. Minimun Limit Flight Level for"
            f"route {db_section.route.indicator} - btw {db_section.point1.indicator} & {db_section.point2.indicator} is"
            f"{db_section.lower_limit_flight_level}."
        )
    if db_section.upper_limit_flight_level and level > db_section.upper_limit_flight_level:
        err["logical_error"].append(
            "Invalid flight level. Upper Limit Flight Level for"
            f"route {db_section.route.indicator} - btw {db_section.point1.indicator} & {db_section.point2.indicator} is"
            f"{db_section.lower_limit_flight_level}."
        )


def validate_fpl_route_section(fpl_section, db_section: RouteSection, data, err):
    domestic_departure, domestic_destination = data["domestic_departure"], data["domestic_destination"]

    # Sample
    # fpl_route_section = {"from": "PON", "to": "URION", "via": "DCT", "speed": "M078", "level": "F330",
    # "top_level": "F330", "flight_rule": "I", "nonessential": "true"}

    # RouteSection Activity Check
    if not db_section.is_active:
        err["logical_error"].append(
            f"Route {db_section.route.indicator} - btw {db_section.point1.indicator} & "
            f"{db_section.point2.indicator} is unavailable."
        )

    # RouteSection Direction Check
    if db_section.direction == "to" and fpl_section["from"] != db_section.point2.indicator:
        err["logical_error"].append(
            "Invalid path direction. Please follow the specified direction rules."
            f"Route {db_section.route.indicator} - {db_section.point1.indicator} to {db_section.point2.indicator}"
        )
    elif db_section.direction == "from" and fpl_section["from"] != db_section.point1.indicator:
        err["logical_error"].append(
            "Invalid path direction. Please follow the specified direction rules."
            f"Route {db_section.route.indicator} - {db_section.point1.indicator} from {db_section.point2.indicator}"
        )

    # TODO: let's have meeting with the authorities to decide how to implement these checks
    # RouteSection Level Verification Check
    # NOTE: Don't forget to validate fpl_section["top_level"] for all case
    fpl_level = fpl_section["level"]
    if fpl_level.startswith("A"):
        check_altitude(fpl_level, db_section, err)

    if fpl_level.startswith("F"):
        check_flight_level(fpl_level, db_section, err)
    ...
    # RouteSection RNAV/RNP Compliance Check (plus rnav level)
    ...
    # RouteSection Mag Track & Track Coloration Compliance Check
    ...
    # RouteSection Availability Based On Nature Of Flight
    if db_section.domestic_only and (not domestic_departure or not domestic_destination):
        err["logical_error"].append(
            "Invalid path usage."
            f"Route {db_section.route.indicator} - btw {db_section.point1.indicator} & {db_section.point2.indicator}"
            "is available only to domestic flights."
        )

    if db_section.not_for_over_flights and (not domestic_departure and not domestic_destination):
        err["logical_error"].append(
            "Invalid path usage."
            f"Route {db_section.route.indicator} - {db_section.point1.indicator} btw {db_section.point2.indicator}"
            "is not available to overflights."
        )
