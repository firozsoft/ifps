"""✘🗸"""
from typing import Union

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.aerodromes.analysis import aerodromes_checks  # noqa
from apps.points.analysis import points_checks  # noqa
from apps.routes.analyses import routes_checks  # noqa


def logical_check(data: dict[str, Union[bool, str, list[dict[str, str]]]]):
    validation_error = None
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

    aerodromes_checks(data, err)
    points_checks(data, err)
    routes_checks(data, err)

    if err["logical_error"]:
        errors = {f"{inx}": err for inx, err in enumerate(err["logical_error"])}
        validation_error = ValidationError(message="Logical Error", params=errors, code="logical_error")

    return validation_error
