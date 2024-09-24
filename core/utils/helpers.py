from itertools import product


def feet_to_flight_level(altitude_feet: float):
    return round(altitude_feet / 100)


def meters_to_flight_level(altitude_meters: float):
    altitude_feet = altitude_meters * 3.28084
    return feet_to_flight_level(altitude_feet)


def generate_routes_from_route_scheme_text(string: str) -> list[str]:
    """Generate routes from route scheme text."""
    return list(map(" ".join, product(*(s.split("/") for s in string.split()))))
