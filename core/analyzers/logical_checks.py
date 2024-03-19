"""✘🗸"""
from typing import Union

from django.conf import settings

from core.analyzers import aerodromes_analysis, route_analysis


def logical_check(data: dict[str, Union[bool, str, list[dict[str, str]]]]):
    err: dict[str, list[str | None]] = {"logical_error": []}

    data["domestic_departure"] = True
    if not data["departure_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in data.keys() and settings.FIR_INDICATOR in data["eet"]
    ):
        data["domestic_departure"] = False

    data["domestic_destination"] = True
    if not data["destination_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in data.keys() and len(data["eet"].split(settings.FIR_INDICATOR)[1].strip()) > 4
    ):
        data["domestic_destination"] = False

    aerodromes_analysis.aerodromes_analyzer(data, err)
    route_analysis.route_analyzer(data, err)

    if err["logical_error"]:
        return {f"{inx}": err for inx, err in enumerate(err["logical_error"])}
