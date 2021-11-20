"""Points Related Checks Module
    this module contains about:
        ✘🗸 Break each section into smaller sections as possible
        ✘🗸 Check compliance with the restrictions of each section:
           ✘🗸 Routes existence
           ✘🗸 Points existence
           ✘🗸 Routes and Points compatibility
           ✘🗸 Level compliance
           ✘🗸 Routes directions compliance
           ✘🗸 Route Schemes compliance
"""
from typing import Union

from apps.routes.models import Route
from apps.utils import Direction
from apps.utils.helper import levels_to_int


def routes_checks(data: dict[str, Union[str, list[dict[str, str]]]], err: dict[str, str]):
    """Check Route Compliance"""
    row_route = data['route'][1:] if data['sid'] else data['route']
    row_route = row_route[1:] if data['star'] else row_route
    mentioned_routes = {section['via'] for section in row_route
                        if section['via'] and section['via'] != "DCT"}

    route_points: dict = {}
    for mentioned_route in mentioned_routes[:]:
        try:
            route_obj = Route.objects.get(name=mentioned_route).select_related('sections')
        except Route.DoesNotExist:
            err['logical_error'] += f"Route {mentioned_route} does not exist. "
        else:
            if not route_obj.is_active:
                err['logical_error'] += f"Route {route_obj} is not active. "
            else:
                route_points[route_obj.name] = (route_obj, route_obj.get_points)

    for row_section in row_route:
        # row_section = {"from": "EHAM",
        #                "to": "LEK",
        #                "via": "LEK2B",
        #                "speed": "K0830",
        #                "level": "F290",
        #                "top_level": "F290",
        #                "flight_rule": "I"}
        from_point, to_point, via = row_section["from"], row_section["to"], row_section["via"]
        if via not in route_points.keys():
            continue
        point_list = route_points[via][1]
        if from_point not in point_list:
            err['logical_error'] += f"Point {from_point} is not on Route {via}. "
        elif to_point not in point_list:
            err['logical_error'] += f"Point {to_point} is not on Route {via}. "
        else:
            sts = (frm_inx := point_list.index(from_point)) > (to_inx := point_list.index(to_point))
            sub_point_list = point_list[frm_inx + (not sts): to_inx + sts: sts][::sts]
            sub_sections_points_tuples = list(zip(sub_point_list[:-1], sub_point_list[1:]))
            for point1, point2 in sub_sections_points_tuples:
                section_obj = route_points[via][0].sections.get(point1=point1, point2=point2)
                if not section_obj.is_active:
                    err['logical_error'] += f"Route {via} between {from_point} and {to_point} is not active. "
                if section_obj.direction != Direction.TO_FROM:
                    if section_obj.direction == Direction.TO and from_point != section_obj.point1:
                        err['logical_error'] += f"Route direction between {from_point} and {to_point}" \
                                                f"is from {section_obj.point1} to {section_obj.point2}. "
                    elif section_obj.direction == Direction.FROM and from_point != section_obj.point2:
                        err['logical_error'] += f"Route direction between {from_point} and {to_point}" \
                                                f"is from {section_obj.point2} to {section_obj.point1}. "
                if levels_to_int(row_section['level']) < section_obj.lower_limit:
                    err['logical_error'] += f"Route {via} Lower Limit exceeded, between {from_point} and " \
                                            f"{to_point}(FL{section_obj.lower_limit}). "
                if levels_to_int(row_section['level']) > section_obj.upper_limit:
                    err['logical_error'] += f"Route {via} Upper Limit exceeded, between {from_point} and " \
                                            f"{to_point}(FL{section_obj.lower_limit}). "
                if row_section['top_level'] != row_section['level'] and \
                        levels_to_int(row_section['top_level']) > section_obj.upper_limit:
                    err['logical_error'] += f"Route {via} Upper Limit exceeded, between {from_point} and " \
                                            f"{to_point}(FL{section_obj.lower_limit}). "

                # TODO: Checks for RNAV/RNP compatibility.
