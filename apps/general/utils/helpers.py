import re
from decimal import Decimal, getcontext


def dms_to_decimal_degrees(coordinate: str) -> tuple[Decimal, Decimal]:
    """Convert degrees or degrees+minutes or degrees+minutes+seconds to decimal-degrees.

    Example: 46N078W -> (46 78) or 4620N07805W -> (46.333333 78.083333)
    """
    pattern = r"^(?P<latitude>(\d{2}|\d{4}|\d{6})(N|S))(?P<longitude>(\d{3}|\d{5}|\d{7})(W|E))$"
    try:
        lat, long = re.match(pattern, coordinate).groupdict().items()
    except AttributeError:
        msg = f"Invalid coordinate: {coordinate}"
        raise ValueError(msg) from None

    def convertor(lat_or_lang, string):
        getcontext().prec = 8
        neg = string[-1] in "SW"
        string = string[:-1]
        spot = lat_or_lang == "latitude"
        deg, minutes = string[: 3 - spot], string[3 - spot :]
        if len(minutes) > 2:
            minutes, seconds = minutes[:2], minutes[2:]
            return (-1) ** neg * (
                Decimal(deg) + Decimal(minutes) / 60 + (Decimal(seconds) / 3600 if seconds else 0)
            )
        return (-1) ** neg * (Decimal(deg) + (Decimal(minutes) / 60 if minutes else 0))

    return convertor(*lat), convertor(*long)
