"""This module contains Helper functions"""
import re
from decimal import Decimal, getcontext


def levels_to_int(row_flight_levels):
    meter = 1
    feet = 3.281 * meter
    if row_flight_levels[0] in ("S", "M"):
        return int(row_flight_levels[1:]) * feet
    return int(row_flight_levels[1:])


def dm2dd(coordinates: str) -> tuple[Decimal, Decimal]:
    """
    Convert degrees or degrees+minutes to decimal-degrees.
    46N078W -> (46 78) or 4620N07805W -> (46.333333 78.083333)
    """
    pattern = r"\b(?P<latitude>\d{2,4}(N|S))(?P<longitude>\d{3,5}(W|E))\b"
    try:
        lat, long = re.match(pattern, coordinates).groupdict().items()
    except AttributeError as attr_error:
        raise ValueError(f"Invalid coordinates: {coordinates}") from attr_error

    def convertor(lat_or_lang, string):
        getcontext().prec = 8
        neg = string[-1] in "SW"
        string = string[:-1]
        spot = lat_or_lang == "latitude"
        deg, minute = string[: 3 - spot], string[3 - spot :]
        return (-1) ** neg * (int(deg) + (Decimal(minute) / 60 if minute else 0))

    return convertor(*lat), convertor(*long)
