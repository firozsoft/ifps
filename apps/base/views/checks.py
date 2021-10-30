import re
from typing import Union

from django.core.exceptions import ValidationError

from ..utils import regex_patterns as rgx_pat


def regex_check(data: dict
                ) -> tuple[dict[str, str], Union[ValidationError, None]]:
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
        'extra': parts[9]
    }
    """
    res = dict()
    err = {'syntax_error': ''}
    if not (callsign := re.match(rgx_pat.CALLSIGN, data['callsign'])):
        err['syntax_error'] += f"callsign({data['callsign']}) is not valid.\n"
    else:
        res['callsign'] = callsign.group()

    if not (flt_rule_type := re.match(rgx_pat.FLIGHT_RULE_TYPE,
                                      data['flt_rule_type'])):
        err['syntax_error'] += f"flight rule/type({data['flt_rule_type']}) is not valid.\n"
    else:
        res['flight_rule'] = flt_rule_type.group('flight_rule')
        res['flight_type'] = flt_rule_type.group('flight_type')

    if not (numbers_type_weak := re.match(rgx_pat.NUMBER_TYPE_WAKE,
            data['numbers_type_weak'])):
        err['syntax_error'] += f"numbers/type/weak({data['numbers_type_weak']}) is not valid.\n"
    else:
        res['ac_numbers'] = numbers_type_weak.group('numbers') or "1"
        res['ac_type'] = numbers_type_weak.group('type')
        res['ac_weak'] = numbers_type_weak.group('weak')

    if not (equp_cpct := re.match(rgx_pat.EQUIPMENTS_CAPACITIES,
            data['equipments_and_capacities'])):
        err['syntax_error'] += f"equipments/capacities({data['equipments_and_capacities']}) is not valid.\n"
    else:
        res['equipments'] = equp_cpct.group('equipments')
        res['capacities'] = equp_cpct.group('capacities')

    if not (dep_ad_time := re.match(rgx_pat.DEPARTURE_AD_TIME,
            data['dep_ad_time'])):
        err['syntax_error'] += f"departure aerodrome or time({data['dep_ad_time']})is not valid.\n"
    else:
        res['departure_ad'] = dep_ad_time.group('dep_ad')
        res['eobt'] = dep_ad_time.group('eobt')

    if not (dest_teet_alt := re.match(rgx_pat.DESTAD_TEET_ALTS,
                                      data['dest_teet_alts'])):
        err['syntax_error'] += f"destination aerodrome or time or alternates({data['dest_teet_alts']}) is not valid.\n"
    else:
        res['destination_ad'] = dest_teet_alt.group('dest_ad')
        res['teet'] = dest_teet_alt.group('teet')
        res['alt_ad_1'] = dest_teet_alt.group('alt1')
        res['alt_ad_2'] = dest_teet_alt.group('alt2')

    if (sts := re.match(rgx_pat.STS, data['others'])):
        res['sts'] = sts.group()
        data['others'].replace(res['sts'], '')
    if (pbn := re.match(rgx_pat.PBN, data['others'])):
        res['pbn'] = pbn.group()
        data['others'].replace(res['pbn'], '')
        res['pbn_rnav_spc'] = pbn.group('rnav_spc')
        res['pbn_rnp_spc'] = pbn.group('rnp_spc')
    if (nav := re.match(rgx_pat.NAV, data['others'])):
        res['nav'] = nav.group()
        data['others'].replace(res['nav'], '')
    if (com := re.match(rgx_pat.COM, data['others'])):
        res['com'] = com.group()
        data['others'].replace(res['com'], '')
    if (dat := re.match(rgx_pat.DAT, data['others'])):
        res['dat'] = dat.group()
        data['others'].replace(res['dat'], '')
    if (sur := re.match(rgx_pat.SUR, data['others'])):
        res['sur'] = sur.group()
        data['others'].replace(res['sur'], '')
    if (dep := re.match(rgx_pat.DEP, data['others'])):
        res['dep'] = dep.group()
        data['others'].replace(res['dep'], '')

    return res, ValidationError(
        message=err['syntax_error'],
        code="syntax_error") if err['syntax_error'] else None
