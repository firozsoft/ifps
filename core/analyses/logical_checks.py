from typing import Union

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.aerodromes.analysis import aerodromes_checks
from apps.points.analysis import points_checks
from apps.routes.analyses.routes_chekcs import routes_checks


def logical_check(data: dict[str, Union[bool, str, list[dict[str, str]]]]):
    validation_error = None
    err: dict[str, str] = {'logical_error': ''}

    data['domestic_dep'] = True
    if not data['departure_ad'].startswith(settings.FIR_FOUR_LETTERS[:2]) \
            or ('eet' in data.keys() and settings.FIR_FOUR_LETTERS in data['eet']):
        data['domestic_dep'] = False
    data['domestic_dest'] = True
    if not data['destination_ad'].startswith(settings.FIR_FOUR_LETTERS[:2]) \
            or 'eet' in data.keys() and len(data['eet'].split(settings.FIR_FOUR_LETTERS)[1].strip()) > 4:
        data['domestic_dest'] = False

    aerodromes_checks(data, err)
    points_checks(data, err)
    routes_checks(data, err)

    if err['syntax_error']:
        validation_error = ValidationError(message=err['logical_error'], code="logical_error")

    return validation_error
