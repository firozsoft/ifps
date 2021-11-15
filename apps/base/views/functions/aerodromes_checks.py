"""
Aerodromes Related Checks Module
    this module contains about:
        ✓ - Aerodromes existence
        ✓ - Aerodromes accept the flight regarding the flight Type
        ✓ - Aerodromes accept the flight regarding the flight Rule
        ✗ TODO: - Aerodromes operational hours and curfews
        ✓ - SID/STAR
"""
import datetime
from typing import Union

from apps.base import models


def aerodromes_checks(data: dict[str, str], err: dict[str, str]):
    """Checks Related To Aerodromes"""

    # NOTE: getting dep, dest and first alt aerodromes
    def _get_ad(four_letters: str) -> Union[models.Aerodrome, None]:
        try:
            ad_model = models.Aerodrome.objects.get(four_letters=four_letters)  # .only("four_letters")
        except models.Aerodrome.DoesNotExist:
            err['logical_error'] += f"{four_letters} does not exist. "
        else:
            if not ad_model.is_active:
                err['logical_error'] += f"{four_letters} is not active. "
            else:
                return ad_model

    if not all([data['departure_ad'], data['destination_ad'], data['alt_ad_1']]):
        err['logical_error'] += "The Destination, Departure and at least one Alternate are Mandatory. "
    else:
        departure_ad = _get_ad(data['departure_ad'])
        destination_ad = _get_ad(data['destination_ad'])
        alt_ad_1 = _get_ad(data['alt_ad_1'])
        if data['alt_ad_2'] is not None:
            alt_ad_2 = _get_ad(data['alt_ad_2'])

    if not all([departure_ad, destination_ad, alt_ad_1]):
        # if any of these is not found or active, then the rest of checks could not be done!
        return

    # NOTE: check dep and dest aerodromes acceptable type of aircraft
    def _check_flight_type_acceptable(ard: models.Aerodrome, fltp: str) -> None:
        if ard.type == 'heliport' and fltp not in ['HEL', 'B212', 'B412']:
            err['logical_error'] += f"{ard} is HELIPORT and isn't applicable for {fltp}(\
                                    accepted types are HEL, B212 and B412). "

    flight_type = data['flight_type']
    _check_flight_type_acceptable(departure_ad, flight_type)
    _check_flight_type_acceptable(destination_ad, flight_type)

    # NOTE: check if dep and dest aerodromes IFR/VFR operation availability
    initial_flight_rule = 'ifr' if data['flight_rule'] in 'IY' else 'vfr'
    if initial_flight_rule not in departure_ad.ifr_vfr:
        err['logical_error'] += f"{departure_ad} does not accept {initial_flight_rule.upper()}. "

    last_flight_rule = 'ifr' if data['route'][-1]['flight_rule'] in 'IY' else 'vfr'
    if last_flight_rule not in departure_ad.ifr_vfr:
        err['logical_error'] += f"{departure_ad} does not accept {last_flight_rule.upper()}. "

    # NOTE: check if dep and dest aerodromes have any restrictions at the time of departure/arrival
    dep_datatime = datetime.datetime.strptime(data['DOF'] + data['eobt'], '%y%m%d%H%M')
    eobt = dep_datatime.time()
    dof = dep_datatime.date()
    estimate_datetime_of_arrival = dep_datatime + datetime.timedelta(hours=int(data['teet'][:2]),
                                                                     minutes=(data['teet'][2:]))
    eta = estimate_datetime_of_arrival.time()
    etd = estimate_datetime_of_arrival.date()

    def _sid_star_exists(sid_star: str, type_: str) -> None:
        if not (it := models.SidStar.objects.get(name=sid_star).first()):
            err['logical_error'] += f"{type_} {sid_star} does not exist. "
        elif type_ not in it.type:
            err['logical_error'] += f"{sid_star}({it.type}) is not of type {type_}. "
        elif type_ == 'SID' and data['departure_ad'] not in it.aerodromes:
            err['logical_error'] += f"SID {sid_star} is not for {departure_ad}. "
        elif type_ == 'STAR' and data['destination_ad'] not in it.aerodromes:
            err['logical_error'] += f"STAR {sid_star} is not for {destination_ad}. "

    if data['sid'] is not None:
        _sid_star_exists(data['sid'], 'SID')
    if data['star'] is not None:
        _sid_star_exists(data['star'], 'STAR')
