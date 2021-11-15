from apps.base.views.functions.aerodromes_checks import aerodromes_checks


def logical_check(data: dict[str, str]):
    # data = {
    # 'callsign', 'flight_rule', 'flight_type', 'ac_numbers', 'ac_type', 'ac_weak', 'equipments', 'capacities',
    # 'departure_ad', 'eobt', 'destination_ad', 'teet', 'alt_ad_1', 'alt_ad_2',
    # 'pbn_rnav_spc', 'pbn_rnp_spc',
    # ..utils.patternsOTHER_INFO_SWITCHES.keys(),
    # 'route'
    # }

    err: dict[str, str] = {'logical_error': ''}
    aerodromes_checks(data, err)


