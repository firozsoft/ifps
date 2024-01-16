from apps.routes.models import RouteSection


def validate_fpl_route_section(fpl_section, db_section: RouteSection, data, err):
    domestic_departure, domestic_destination = data["domestic_departure"], data["domestic_destination"]

    # Sample
    # fpl_route_section = {"from": "PON", "to": "URION", "via": "DCT", "speed": "M078", "level": "F330",
    # "top_level": "F330", "flight_rule": "I", "section_doesnt_need_check": "true"}

    # RouteSection Activity Check
    if not db_section.is_active:
        err["logical_error"].append(
            f"Route {db_section.route.name} - between {db_section.point1.name} & "
            f"{db_section.point2.name} is unavailable."
        )

    # RouteSection Direction Check
    if db_section.direction == "to" and fpl_section["from"] != db_section.point2.name:
        err["logical_error"].append(
            "Invalid path direction. Please follow the specified direction rules."
            f"Route {db_section.route.name} - {db_section.point1.name} to {db_section.point2.name}"
        )
    elif db_section.direction == "from" and fpl_section["from"] != db_section.point1.name:
        err["logical_error"].append(
            "Invalid path direction. Please follow the specified direction rules."
            f"Route {db_section.route.name} - {db_section.point1.name} from {db_section.point2.name}"
        )

    # TODO: let's have meeting with the authorities to decide how to implement these checks
    # RouteSection Level Verification Check
    # NOTE: Don't forget to validate fpl_section["top_level"] for all case
    if fpl_section["level"].startswith("A"):
        level = int(fpl_section["level"].replace("A", ""))
        if db_section.minimum_safe_altitude and level < db_section.minimum_safe_altitude:
            err["logical_error"].append(
                "Invalid altitude. Minimun Safe Altitude for"
                f"route {db_section.route.name} - {db_section.point1.name} between {db_section.point2.name} is"
                f"{db_section.minimum_safe_altitude}."
            )
        if db_section.lower_limit_altitude and level < db_section.lower_limit_altitude:
            err["logical_error"].append(
                "Invalid altitude. Minimun Limit Altitude for"
                f"route {db_section.route.name} - {db_section.point1.name} between {db_section.point2.name} is"
                f"{db_section.lower_limit_altitude}."
            )
        if db_section.upper_limit_altitude and level > db_section.upper_limit_altitude:
            err["logical_error"].append(
                "Invalid altitude. Upper Limit Altitude for"
                f"route {db_section.route.name} - {db_section.point1.name} between {db_section.point2.name} is"
                f"{db_section.lower_limit_altitude}."
            )

    if fpl_section["level"].startswith("F"):
        level = int(fpl_section["level"].replace("F", ""))
        if db_section.minimum_safe_flight_level and level < db_section.minimum_safe_flight_level:
            err["logical_error"].append(
                "Invalid flight level. Minimun Safe Flight Level for"
                f"route {db_section.route.name} - {db_section.point1.name} between {db_section.point2.name} is"
                f"{db_section.minimum_safe_flight_level}."
            )
        if db_section.lower_limit_flight_level and level < db_section.lower_limit_flight_level:
            err["logical_error"].append(
                "Invalid flight level. Minimun Limit Flight Level for"
                f"route {db_section.route.name} - {db_section.point1.name} between {db_section.point2.name} is"
                f"{db_section.lower_limit_flight_level}."
            )
        if db_section.upper_limit_flight_level and level > db_section.upper_limit_flight_level:
            err["logical_error"].append(
                "Invalid flight level. Upper Limit Flight Level for"
                f"route {db_section.route.name} - {db_section.point1.name} between {db_section.point2.name} is"
                f"{db_section.lower_limit_flight_level}."
            )
    ...
    # RouteSection RNVA/RNP Compliance Check (plus rnav level)
    ...
    # RouteSection Mag Track & Track Coloration Compliance Check
    ...
    # RouteSection Mag Track & Track Coloration Compliance Check
    ...
    # RouteSection Availability Based On Nature Of Flight
    if db_section.domestic_only and (not domestic_departure or not domestic_destination):
        err["logical_error"].append(
            "Invalid path usage."
            f"Route {db_section.route.name} - {db_section.point1.name} btw {db_section.point2.name}"
            "is available only to domestic flights."
        )

    if db_section.not_for_over_flights and (not domestic_departure and not domestic_destination):
        err["logical_error"].append(
            "Invalid path usage."
            f"Route {db_section.route.name} - {db_section.point1.name} btw {db_section.point2.name}"
            "is not available to overflights."
        )
