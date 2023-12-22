"""Points Related Checks Module
    this module contains about:
        🗸 Break each section into smaller sections as possible
        🗸 Check compliance with the restrictions of each section:
           🗸 Routes existence
           🗸 Routes and Points compatibility
           🗸 Level compliance
           🗸 Routes directions compliance
           🗸 Route Schemes compliance
"""
import json
from typing import Union

from apps.routes.models import Route
from apps.utils import Direction
from apps.utils.helpers import levels_to_FL_int


def _find_sections(route_name, start_point_name, end_point_name, sections_dict, err):
    # sections_dict[route_name] => {(p1, p2): sectionX, (p2, p3): sectionY, ...}

    if not [True if end_point_name in tp else False for dct in sections_dict[route_name] for tp in dct].pop():
        # No RouteSection contains the end point
        err["logical_error"].append(f"On route {route_name}, no section contains {end_point_name} +.")
        return None

    found = False
    sections = []
    start_point_name_seen_once = False
    for dct in sections_dict[route_name]:
        # Go through sections of this route
        for tp in dct:
            # Check if any section contains the start point
            # this at most happens twice(as p1 or as p2) so go looping if required
            # to understand the code below look at the doc-ed code benithe it
            if start_point_name in tp and not found:
                start_point_name_seen_once = True
                index = start_point_name == tp[0]  # use boolean as index to make code reusable in loop
                sections.append(dct[tp])
                second_point_name = tp[index]
                for tp2 in dct:
                    if tp2[not index] == second_point_name:
                        second_point_name = tp2[index]
                        sections.append(dct[tp2])
                    if second_point_name == end_point_name:
                        found = True
                        break

                """
                # In case start point is as point1 of the section
                if start_point_name == tp[0]:
                    sections.append(dct[tp])
                    second_point_name = tp[1]
                    for tp2 in dct:
                        if tp2[0] == second_point_name:
                            second_point_name = tp[1]
                            sections.append(dct[tp])
                        if second_point_name == end_point_name:
                            found = True
                            break
                # Otherwise start point is point2 of the section but go looping if not already found the last section
                elif not found:
                    sections.append(dct[tp])
                    second_point_name = tp[0]
                    for tp2 in dct:
                        if tp2[1] == second_point_name:
                            second_point_name = tp[0]
                            sections.append(dct[tp])
                        if second_point_name == end_point_name:
                            found = True
                            break
                """

        else:
            # No connection between start and end points have been found
            err["logical_error"].append(
                f"On route {route_name}, no connection between {start_point_name} and {end_point_name} exists."
            )
            return None

    if not start_point_name_seen_once:
        # No RouteSection contains the start point
        err["logical_error"].append(f"On route {route_name}, no section contains {end_point_name} -.")
        return None

    return sections


def routes_checks(data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str | None]]):
    """Check Route Compliance"""
    # if data["sid"] or data["star"] exists so the first or last item of route is sid or star and must be ignored here
    # this has been done already in points-check
    print(json.dumps(data["route"]))
    route_names_to_check = {
        section["via"] for section in data["route"] if section["via"] and section.get("needs_check", True)
    }

    route_points: dict = {}
    existing_routes = Route.objects.filter(name__in=route_names_to_check).prefetch_related("sections")
    route_objects: dict[str, Route] = {
        route.name: route for route in existing_routes
    }  # Useing hash-map to avoid multiple db query in loop
    for route_name in route_names_to_check:
        route_obj = route_objects.get(route_name)
        if route_obj is None:
            err["logical_error"].append(f"Route {route_name} does not exist.")
        else:
            route_points[route_name] = (route_obj, route_obj.get_points())
            if not route_obj.is_active:
                err["logical_error"].append(f"Route {route_name} is not active.")

    for row_section in data["route"]:
        # row_section = {"from": "EHAM", "to": "LEK",  "via": "LEK2B",
        # "speed": "K0830",  "level": "F290",  "top_level": "F290",  "flight_rule": "I"}
        from_point, to_point, via = (
            row_section["from"],
            row_section["to"],
            row_section["via"],
        )
        if via not in route_points.keys():
            continue

        point_set = route_points[via][1]
        if from_point not in point_set:
            err["logical_error"].append(f"Point {from_point} is not on Route {via}.")
        if to_point not in point_set:
            err["logical_error"].append(f"Point {to_point} is not on Route {via}.")

        entered, exited = False, False
        sts = (frm_inx := point_set.index(from_point)) > (to_inx := point_set.index(to_point))
        sub_point_set = point_set[frm_inx + (not sts) : to_inx + sts : sts][::sts]
        db_route_section_points = list(zip(sub_point_set[:-1], sub_point_set[1:]))
        for point1, point2 in db_route_section_points:
            if (
                not entered
                and "entrance_section" in data.keys()
                and (point1, point2)
                != (
                    data["entrance_section"].point1,
                    data["entrance_section"].point2,
                )
            ):
                continue

            entered = True
            section_obj = route_points[via][0].sections.get(point1=point1, point2=point2)
            if not section_obj.is_active:
                err["logical_error"] += f"Route {via} between {from_point} and {to_point} is not active. "
            if section_obj.direction != Direction.TO_FROM:
                if section_obj.direction == Direction.TO and from_point != section_obj.point1:
                    err["logical_error"] += (
                        f"Route direction between {from_point} and {to_point}"
                        f"is from {section_obj.point1} to {section_obj.point2}. "
                    )
                elif section_obj.direction == Direction.FROM and from_point != section_obj.point2:
                    err["logical_error"] += (
                        f"Route direction between {from_point} and {to_point}"
                        f"is from {section_obj.point2} to {section_obj.point1}. "
                    )
            if levels_to_FL_int(row_section["level"]) < section_obj.lower_limit:
                err["logical_error"] += (
                    f"Route {via} Lower Limit exceeded, between {from_point} and "
                    f"{to_point}(FL{section_obj.lower_limit}). "
                )
            if levels_to_FL_int(row_section["level"]) > section_obj.upper_limit:
                err["logical_error"] += (
                    f"Route {via} Upper Limit exceeded, between {from_point} and "
                    f"{to_point}(FL{section_obj.lower_limit}). "
                )
            if (
                row_section["top_level"] != row_section["level"]
                and levels_to_FL_int(row_section["top_level"]) > section_obj.upper_limit
            ):
                err["logical_error"] += (
                    f"Route {via} Upper Limit exceeded, between {from_point} and "
                    f"{to_point}(FL{section_obj.lower_limit}). "
                )

            # TODO: Checks for RNAV/RNP compatibility.

            if "exit_section" in data.keys() and (point1, point2) != (
                data["exit_section"].point1,
                data["exit_section"].point2,
            ):
                break
