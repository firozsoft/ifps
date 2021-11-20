"""Points Related Checks Module
    this module contains about:
        ✓ DEP, DEST and ALTN Reference Points existence
"""
import re
from typing import Union

from apps.points.models import Point
from apps.utils.regex_patterns import BEARING_DIST, SIG_POINT


def points_checks(data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, str]):
    if data['domestic_dep'] and data['departure_ad'] in ("ZZZZ", "AFIL"):
        matched_dict = re.match(SIG_POINT, data['dep']).groupdict()
        point = matched_dict['ref_point'] or matched_dict['point']
        if point is not None and not Point.objects.filter(point=point).exists():
            err['logical_error'] += f"ITEM18 DEP/{data['dep']}, Point {point} does not exist. "

    if data['domestic_dest'] and  data['destination_ad'] == "ZZZZ":
        matched_dict = re.match(SIG_POINT, data['dest']).groupdict()
        point = matched_dict['ref_point'] or matched_dict['point']
        if point is not None and not Point.objects.filter(point=point).exists():
            err['logical_error'] += f"ITEM18 DEST/{data['dest']}, Point {point} does not exist. "

    if all([data['domestic_dep'], data['domestic_dest']]) and \
            (data['alt_ad_1'] == "ZZZZ" or data['alt_ad_2'] == "ZZZZ"):
        if point := re.match(BEARING_DIST, data['altn']):
            if not Point.objects.filter(point=point.group('ref_point')).exists():
                err['logical_error'] += f"ITEM18 ALTN/{data['altn']}, Point {point} does not exist. "
