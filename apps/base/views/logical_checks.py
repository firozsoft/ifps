from apps.base import models


def logical_check(data: dict[str, str]):
    # data = {
    # 'callsign', 'flight_rule', 'flight_type', 'ac_numbers', 'ac_type', 'ac_weak', 'equipments', 'capacities',
    # 'departure_ad', 'eobt', 'destination_ad', 'teet', 'alt_ad_1', 'alt_ad_2',
    # 'pbn_rnav_spc', 'pbn_rnp_spc',
    # ..utils.patternsOTHER_INFO_SWITCHES.keys(),
    # 'route'
    # }

    err: dict[str, str] = {'logical_error': ''}
    for ad in (data['departure_ad'], data['destination_ad'], data['alt_ad_1'], data['alt_ad_2']):
        if ad is not None and not models.Aerodrome.objects.filter(four_letters=data['dep']).exists():
            err['logical_error'] += f"{ad} does not exist. "

    def _sid_star_exists(sid_star: str, type_: str) -> None:
        if not (it := models.SidStar.objects.get(name=sid_star).first()):
            err['logical_error'] += f"{type_} {sid_star} does not exist. "
        elif type_ not in it.type:
            err['logical_error'] += f"{sid_star}({it.type}) is not of type {type_}. "
        elif type_ == 'SID' and data['departure_ad'] not in it.aerodromes:
            err['logical_error'] += f"SID {sid_star} is not for {data['departure_ad']}. "
        elif type_ == 'STAR' and data['destination_ad'] not in it.aerodromes:
            err['logical_error'] += f"STAR {sid_star} is not for {data['destination_ad']}. "

    if data['sid'] is not None:
        _sid_star_exists(data['sid'], 'SID')
    if data['star'] is not None:
        _sid_star_exists(data['star'], 'STAR')

    pass
