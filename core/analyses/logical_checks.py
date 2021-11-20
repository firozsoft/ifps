from typing import Union

from django.core.exceptions import ValidationError

from apps.aerodromes.analysis import aerodromes_checks
from apps.points.analysis import points_checks
from apps.routes.analyses.routes_chekcs import routes_checks


def logical_check(data: dict[str, Union[str, list[dict[str, str]]]]):

    validation_error = None
    err: dict[str, str] = {'logical_error': ''}

    aerodromes_checks(data, err)
    points_checks(data, err)
    routes_checks(data, err)

    if err['syntax_error']:
        validation_error = ValidationError(message=err['logical_error'], code="logical_error")

    return validation_error
