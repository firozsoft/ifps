from apps.aerodromes.analysis import aerodromes_checks
from apps.points.analysis import points_checks
from apps.routes.analyses.routes_chekcs import routes_checks


def logical_check(data: dict[str, str]):
    # data = {
    # 'call_sign', 'flight_rule', 'flight_type', 'ac_numbers', 'ac_type', 'ac_weak', 'equipments', 'capacities',
    # 'departure_ad', 'eobt', 'destination_ad', 'teet', 'alt_ad_1', 'alt_ad_2',
    # 'pbn_rnav_spc', 'pbn_rnp_spc',
    # ..utils.patternsOTHER_INFO_SWITCHES.keys(),
    # 'route'
    # }

    err: dict[str, str] = {'logical_error': ''}
    aerodromes_checks(data, err)
    points_checks(data, err)
    routes_checks(data, err)
