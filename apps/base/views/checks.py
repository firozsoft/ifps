import re
from datetime import datetime
from typing import Union

from django.core.exceptions import ValidationError

from ..utils import regex_patterns as rgx_pat
from ..utils.patterns import OTHER_INFO_SWITCHES


def regex_check(data: dict) -> tuple[dict[str, str], Union[ValidationError, None]]:
    """
    data = {
        'callsign': parts[1],
        'flt_rule_type': parts[2],
        'numbers_type_weak': parts[3],
        'equipments_and_capacities': parts[4],
        'dep_ad_time': parts[5],
        'dest_teet_alts': parts[7],
        ----
        'route': parts[6],
        'others': parts[8],
        # 'extra': parts[9]
    }
    """
    res = dict()
    err = {'syntax_error': ''}
    if not (callsign := re.match(rgx_pat.CALLSIGN, data['callsign'])):
        err['syntax_error'] += f"callsign({data['callsign']}) is not valid. "
    else:
        res['callsign'] = callsign.group()

    if not (flt_rule_type := re.match(rgx_pat.FLIGHT_RULE_TYPE,
                                      data['flt_rule_type'])):
        err['syntax_error'] += f"flight rule/type({data['flt_rule_type']}) is not valid. "
    else:
        res['flight_rule'] = flt_rule_type.group('flight_rule')
        res['flight_type'] = flt_rule_type.group('flight_type')

    if not (numbers_type_weak := re.match(rgx_pat.NUMBER_TYPE_WAKE,
                                          data['numbers_type_weak'])):
        err['syntax_error'] += f"numbers/type/weak({data['numbers_type_weak']}) is not valid. "
    else:
        res['ac_numbers'] = numbers_type_weak.group('numbers') or "1"
        res['ac_type'] = numbers_type_weak.group('type')
        res['ac_weak'] = numbers_type_weak.group('weak')

    if not (equp_cpct := re.match(rgx_pat.EQUIPMENTS_CAPACITIES,
                                  data['equipments_and_capacities'])):
        err['syntax_error'] += f"equipments/capacities({data['equipments_and_capacities']}) is not valid. "
    else:
        res['equipments'] = equp_cpct.group('equipments')
        res['capacities'] = equp_cpct.group('capacities')

    if not (dep_ad_time := re.match(rgx_pat.DEPARTURE_AD_TIME,
                                    data['dep_ad_time'])):
        err['syntax_error'] += f"departure aerodrome or time({data['dep_ad_time']})is not valid. "
    else:
        res['departure_ad'] = dep_ad_time.group('dep_ad')
        res['eobt'] = dep_ad_time.group('eobt')

    if not (dest_teet_alt := re.match(rgx_pat.DESTAD_TEET_ALTS,
                                      data['dest_teet_alts'])):
        err['syntax_error'] += f"destination aerodrome or time or alternates({data['dest_teet_alts']}) is not valid. "
    else:
        res['destination_ad'] = dest_teet_alt.group('dest_ad')
        res['teet'] = dest_teet_alt.group('teet')
        res['alt_ad_1'] = dest_teet_alt.group('alt1')
        res['alt_ad_2'] = dest_teet_alt.group('alt2')

    other_info = data['others'].split()
    last_switch_index = 0
    for item in other_info[:]:
        if not item.count('/'):
            other_info[last_switch_index] += " " + item
            other_info.remove(item)
        else:
            last_switch_index = other_info.index(item)
    for item in other_info[:]:
        for key, pattern in OTHER_INFO_SWITCHES.items():
            if item.startswith(f"{key}/"):
                if matched := re.match(pattern, item):
                    res[key.lower()] = matched.group(key)
                    if key == 'PBN':
                        res['pbn_rnav_spc'] = matched.group('rnav_spc')
                        res['pbn_rnp_spc'] = matched.group('rnp_spc')
                    elif key == 'DOF':
                        try:
                            datetime.strptime(res[key.lower()], '%y%m%d')
                        except ValueError:
                            err['syntax_error'] += f"DOF({res[key.lower()]}) is not in valid(YYMMDD). "
                else:
                    err['syntax_error'] += f"{item} is not valid. "

        else:
            err['syntax_error'] += f"{item} is not valid syntax for OTHER INFO"

    route_items = data['route'].split()
    if not (init_sp_lvl := re.match(rgx_pat.SPEED_LEVEL, route_items[0])):
        err['syntax_error'] += f"{route_items[0]} must be a valid speed & level"
    else:
        res['initial_speed'] = init_sp_lvl.group('speed')
        res['initial_level'] = init_sp_lvl.group('level')

    # route_items[1] must be a valid (DCT or ats route or point)
    previous = dict()  # previous scrutinized item
    if item := re.match(rgx_pat.ROUTE, route_items[1]):
        previous = {'type': 'route', 'item': item.group('route')}
    elif item := re.match(rgx_pat.SID_STAR, route_items[1]):
        previous = {'type': 'route', 'item': item.group('sid_star')}
    elif route_items[1] == "DCT":
        previous = {'type': 'dct', 'item': "DCT"}
    elif item := re.match(rgx_pat.POINT, route_items[1]):
        previous = {'type': 'point', 'item': item.group('point')}
    elif item := re.match(rgx_pat.BEARING_DIST, route_items[1]):
        previous = {'type': 'point', 'item': item.group('ref_point')}
    else:
        err['syntax_error'] += f"{route_items[1]} must be a valid ATS Route or DCT or an ATS Point"

    if previous:
        # route segments
        segments = [{
            'from': res['departure_ad'],
            'to': previous['item'] if previous['type'] == 'point' else '',
            'via': previous['item']
            if previous['type'] in ('route', 'dct') else '',
            'speed': res['initial_speed'],
            'level': res['initial_level'],
            'top_level': res['initial_level'],
            'flight_rule': res['flight_rule'],
        }]
        # previous['type'] == 'route' | 'dct' | 'point' | 'sig_point'
        for item in route_items[2:]:
            if previous['type'] == 'route':
                for pat in (
                        rgx_pat.POINT,
                        rgx_pat.CHANGE_SPEED_LEVEL,
                        rgx_pat.CRUISECLIMB):
                    if it := re.match(pat, item):
                        previous = {'type': 'point', 'item': it.group('point')}
                        segments[-1]['to'] = previous['item']
                        segments.append(
                            {'from': previous['item'],
                             'to': '',
                             'via': '',
                             'speed': segments[-1]['speed'],
                             'level': segments[-1]['level'],
                             'top_level': segments[-1]['top_level'],
                             'flight_rule': segments[-1]['flight_rule'], })
                        if pat != rgx_pat.POINT:
                            segments[-1]['speed'] = it.group('speed')
                            segments[-1]['level'] = it.group('level')
                        if pat == rgx_pat.CRUISECLIMB:
                            segments[-1]['top_level'] = it.group('top_level')
                        break
                else:
                    err['syntax_error'] += f"{item} must be a valid ATS Point. "
                    break
            if previous['type'] == 'dct':
                was_sig_point = False
                if (it := re.match(rgx_pat.COR_DEGREES, item)):
                    was_sig_point = True
                    previous = {'type': 'sig_point',
                                'item': it.group('degrees')}
                elif (it := re.match(rgx_pat.COR_DEG_MINS, item)):
                    was_sig_point = True
                    previous = {'type': 'sig_point',
                                'item': it.group('deg_min')}
                elif (it := re.match(rgx_pat.BEARING_DIST, item)):
                    was_sig_point = True
                    previous = {'type': 'sig_point',
                                'item': it.group('point')}
                elif (it := re.match(rgx_pat.POINT, item)):
                    was_sig_point = True
                    previous = {'type': 'point',
                                'item': it.group('point')}
                if was_sig_point:
                    segments[-1]['to'] = previous['item']
                    segments.append({
                        'from': previous['item'],
                        'to': '',
                        'via': '',
                        'speed': segments[-1]['speed'],
                        'level': segments[-1]['level'],
                        'top_level': segments[-1]['top_level'],
                        'flight_rule': segments[-1]['flight_rule'], })
                else:
                    err['syntax_error'] += f"{item} must be a valid Significant Point. "
                    break

        res['route'] = segments

    return res, ValidationError(
        message=err['syntax_error'],
        code="syntax_error") if err['syntax_error'] else None
