"""Points Related Checks Module
    this module contains about:
        🗸 DEP, DEST and ALTN Reference Points existence
        🗸 Points existence
        🗸 Points active/us
        🗸 Determine entry/exit point(s) if required
        🗸 Determine entry/exit route-section(s) if required
"""
import re
from typing import Union

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import F, Q

from apps.points.models import Point
from apps.utils.regex_patterns import BEARING_DIST, SIG_POINT


def points_checks(
        data: dict[str, Union[bool, str, list[dict[str, str]]]],
        err: dict[str, str]):
    if data['domestic_dep'] and data['departure_ad'] in ("ZZZZ", "AFIL"):
        matched_dict = re.match(SIG_POINT, data['dep']).groupdict()
        point = matched_dict['ref_point'] or matched_dict['point']
        if point is not None and not Point.objects.filter(
                point=point).exists():
            err['logical_error'] += f"ITEM18 DEP/{data['dep']}, Point {point} does not exist. "

    if data['domestic_dest'] and data['destination_ad'] == "ZZZZ":
        matched_dict = re.match(SIG_POINT, data['dest']).groupdict()
        point = matched_dict['ref_point'] or matched_dict['point']
        if point is not None and not Point.objects.filter(
                point=point).exists():
            err['logical_error'] += f"ITEM18 DEST/{data['dest']}, Point {point} does not exist. "

    if all([data['domestic_dep'], data['domestic_dest']]) and \
            (data['alt_ad_1'] == "ZZZZ" or data['alt_ad_2'] == "ZZZZ"):
        if point := re.match(BEARING_DIST, data['altn']):
            if not Point.objects.filter(
                    point=point.group('ref_point')).exists():
                err['logical_error'] += f"ITEM18 ALTN/{data['altn']}, Point {point} does not exist. "

    # checks related to route
    row_route = data['route'][1:] if data['sid'] else data['route']
    row_route = row_route[1:] if data['star'] else row_route
    mentioned_points = set()
    _ = [
        (mentioned_points.add(
            section['from']), mentioned_points.add(
            section['to'])) for section in row_route]

    entered = False if not data['domestic_dep'] else True
    exited = False if not data['domestic_dest'] else True
    entry_point = before_entry_point = after_entry_point = None
    exit_point = before_exit_point = after_exit_point = None
    eets = data['eet'].split(settings.FIR_FOUR_LETTERS)
    previous_fir, next_fir = (
        eets[0],
        eets[1]) if len(eets) > 1 else(
        None, eets[0])

    for mentioned_point in mentioned_points:
        try:
            point_obj = Point.objects.get(
                name=mentioned_point).prefetch_related(
                'fir', 'fir_boundaries')
        except Point.DoesNotExist:
            err['logical_error'] += f"Point {mentioned_point} does not exist. "
        else:
            if not point_obj.is_active:
                err['logical_error'] += f"Point {mentioned_point} is not active. "
            if not entered:
                if point_obj.fir.filter(
                        name=settings.FIR_FOUR_LETTERS).exists():
                    entered, after_entry_point = True, point_obj
                    if point_obj.is_fir_boundary:
                        entry_point = mentioned_point
                else:
                    before_entry_point = point_obj
            if not exited:
                # HINT: maybe we should use Q instead of F!
                if point_obj.fir.filter(
                        ~F(name=settings.FIR_FOUR_LETTERS)).exists():
                    exited, after_exit_point = True, point_obj
                    if point_obj.is_fir_boundary:
                        exit_point = mentioned_point
                else:
                    before_exit_point = point_obj

    if entry_point:
        row_route = row_route[row_route.index(entry_point):]
    if exit_point:
        row_route = row_route[:row_route.index(exit_point) + 1]

    if not (
            entered and exited) and settings.FIR_FOUR_LETTERS not in data['eet']:
        err['logical_error'] += f"Not domestic nor Overflight for {settings.FIR_FOUR_LETTERS}. "

    else:
        def _find_row_section(point1, point2):
            return [
                section for section in row_route if (
                    section['from'], section['to']) in [
                    (point1, point2), (point2, point1)]][0]

        def _find_section(
                before_x_point,
                after_x_point,
                x_fir,
                next_or_prev_fir='prev'):
            section = _find_row_section(
                before_x_point.name, after_x_point.name)
            x_route = section['via']
            psb_x_points = before_x_point.fir_boundaries.intersection(
                after_x_point.fir_boundaries)
            if psb_x_points.count() == 1:
                x_point = psb_x_points.first()
            elif psb_x_points.count() > 1:
                if not x_fir:
                    if next_or_prev_fir == 'next':
                        x_fir = after_x_point.fir.filter(
                            name__startswith=data['destination_ad'][:2])
                    else:
                        x_fir = before_x_point.fir.filter(
                            name__startswith=data['departure_ad'][:2])

                psb_x_points = psb_x_points.filter(fir=x_fir)
                if psb_x_points.count() == 1:
                    x_point = psb_x_points.first()
                else:
                    for psb_x_point in psb_x_points:
                        if psb_x_point.route_sections1.filter(
                                route__name=x_route).exists():
                            x_point = psb_x_point
                            break
                        elif psb_x_point.route_sections2.filter(route__name=x_route).exists():
                            x_point = psb_x_point
                            break
                    else:
                        raise ValidationError(
                            message=f"Something goes wrong! psb_entry_points={psb_x_points}",
                            code="500 serverside error")
            else:
                raise ValidationError(
                    message=f"Something goes wrong! can't find entry point",
                    code="500 serverside error")
            return x_point.route_sections1 \
                if x_point.route_sections1.point2.fir.name == settings.FIR_FOUR_LETTERS \
                else x_point.route_sections2

        if not data['domestic_dep']:
            data['entrance_section'] = _find_section(
                before_entry_point, after_entry_point, previous_fir)
        if not data['domestic_dest']:
            data['exit_section'] = _find_section(
                before_exit_point, after_exit_point, next_fir, 'next')
