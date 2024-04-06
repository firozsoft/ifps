from apps.routes.models.route_section import RouteSection


def check_altitude(level, db_section: RouteSection, err):
    level = int(level.replace("A", ""))
    if db_section.minimum_safe_altitude and level < db_section.minimum_safe_altitude:
        err["logical_error"].append(
            f"Minimun Safe Altitude for route {db_section} is {db_section.minimum_safe_altitude}."
        )
    if db_section.lower_limit_altitude and level < db_section.lower_limit_altitude:
        err["logical_error"].append(
            f"Minimun Limit Altitude for route {db_section} is {db_section.lower_limit_altitude}."
        )
    if db_section.upper_limit_altitude and level > db_section.upper_limit_altitude:
        err["logical_error"].append(
            f"Upper Limit Altitude for route {db_section} is {db_section.lower_limit_altitude}."
        )


def check_flight_level(level, db_section: RouteSection, err):
    level = int(level.replace("F", ""))
    if db_section.minimum_safe_flight_level and level < db_section.minimum_safe_flight_level:
        err["logical_error"].append(
            f"Minimun Safe Flight Level for route {db_section} is {db_section.minimum_safe_flight_level}."
        )
    if db_section.lower_limit_flight_level and level < db_section.lower_limit_flight_level:
        err["logical_error"].append(
            f"Minimun Limit Flight Level for route {db_section} is {db_section.lower_limit_flight_level}."
        )
    if db_section.upper_limit_flight_level and level > db_section.upper_limit_flight_level:
        err["logical_error"].append(
            f"Upper Limit Flight Level for route {db_section} is {db_section.lower_limit_flight_level}."
        )


def validate_fpl_route_section(fpl_section, db_section: RouteSection, data, err):
    domestic_departure, domestic_destination = data["domestic_departure"], data["domestic_destination"]

    # Sample
    # fpl_route_section = {"from": "PON", "to": "URION", "via": "DCT", "speed": "M078", "level": "F330",
    # "top_level": "F330", "flight_rule": "I", "nonessential": "true"}

    route = db_section.route
    point1 = db_section.point1
    point2 = db_section.point2

    # Availability check
    if not db_section.is_active:
        err["logical_error"].append(f"Route {db_section} is unavailable.")
    if not route.is_active:
        err["logical_error"].append(f"Route {route} is unavailable.")
    if not point1.is_active:
        err["logical_error"].append(f"Route {point1} is unavailable.")
    if not point2.is_active:
        err["logical_error"].append(f"Route {point2} is unavailable.")

    # Direction check
    if db_section.direction == "to" and fpl_section["from"] != point2:
        err["logical_error"].append(f"Invalid path direction. Route {route} - {point1} to {point2}")
    elif db_section.direction == "from" and fpl_section["from"] != point1:
        err["logical_error"].append(f"Invalid path direction. Route {route} - {point1} from {point2}")

    # TODO: let's have meeting with the authorities to decide how to implement these checks
    # Level verification
    for fpl_level in (fpl_section["level"], fpl_section["top_level"]):
        if fpl_level.startswith("A"):
            check_altitude(fpl_level, db_section, err)

        if fpl_level.startswith("F"):
            check_flight_level(fpl_level, db_section, err)
    ...
    # RouteSection RNAV/RNP Compliance Check (plus rnav level)
    ...
    # RouteSection Mag Track & Track Coloration Compliance Check
    ...
    # RouteSection Availability Based On Nature Of Flight (domestic/transiting/local-dep/dest)
    if db_section.domestic_only and (not domestic_departure or not domestic_destination):
        err["logical_error"].append(
            "Invalid path usage." f"Route {db_section} is available only to domestic flights."
        )

    if db_section.not_for_over_flights and (not domestic_departure and not domestic_destination):
        err["logical_error"].append(
            "Invalid path usage." f"Route {db_section} is not available to overflights."
        )
