"""Route Item Related Checks Module
    in this module:
        🗸 Determine portion of the route needs to be checked
        🗸 Routes/Points existence & active/us
        🗸 Routes and Points correlation
        🗸 Route-Sections adherence
        🗸 Route Schemes adherence

    In order to be able to check the route item there are 4 possible situations as follows:
       1. Both departure and destination of the flight are within our FIR, so it's a domestic flight
       2. Only departure is inside our FIR, so it's a domestic departure or domestic_dep
       3. Only destination is inside our FIR, so it's a domestic destination or domestic_dest
       4. Neither departure nor destination aren't inside our FIR, so it's an overflight

    based on these situations here we have to analyse the whole route or a portion there of which is located
    within our FIR. Since for a flight conducting international operation it is mandatory to use EET in
    item 18 of its flight plan we can take advantages of this and looking at previous or next FIRs in EET
    in respect of our FIR we can determine the entry route/point and/or exit route/point

    * if flight is departed from an adjacent FIR in the EET it have to start with our FIR so the previous FIR
    have to be determined using the first two letters of the departure Ad. and the FIR queryset from database.
"""
import copy
import re
from typing import Union

import networkx as nx
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from apps.points.models import Point
from core.analyzers import error_messages as errors
from core.analyzers.limit_route_portion import normalize_route_portions
from core.analyzers.route_section_validation import validate_fpl_route_section
from core.utils.regex_patterns import AERODROME, SIG_POINT


def find_all_nested_real_sections(fpl_route_section: dict[str, str], db_sections: tuple[str, str, str]):
    route, start_point, end_point = (
        fpl_route_section["via"],
        fpl_route_section["from"],
        fpl_route_section["to"],
    )

    db_route_sections = {tp for tp in db_sections if tp[0] == route}

    # Create an undirected graph
    G = nx.Graph()

    # Add edges to the graph representing route sections
    for tp in db_route_sections:
        G.add_edge(tp[1], tp[2], route=tp[0])

    try:
        # Use shortest_path to find the only path
        path = nx.shortest_path(G, source=start_point, target=end_point)

    except nx.NetworkXException:
        raise ValidationError(errors.PATH_NOT_FOUND.format(start_point, end_point, route))

    # Filter out edges to get the actual sections
    return [(G[u][v]["route"], u, v) for u, v in zip(path[:-1], path[1:]) if G.has_edge(u, v)]


def eet_is_correct(data, err: dict[str, list[str]]) -> bool:
    if not data["eet"]:
        err["logical_error"].append(errors.EET_NOT_FOUND)
        return False
    if settings.FIR_INDICATOR not in data["eet"] and not data["domestic_departure"]:
        err["logical_error"].append(errors.FIR_NOT_FOUND_IN_EET.format(settings.FIR_INDICATOR))
        return False
    return True


def retrieve_point_name_and_add_to_set(point_names: set, string: str):
    if re.match(AERODROME, string):
        # to ignore aerodromes referenced in item 18 as dep, dest, altn, ralt, talt
        return
    matched = re.match(SIG_POINT, string)
    if matched is not None:
        point_name = matched.groupdict().get("point", None) or matched.groupdict().get("ref_point", None)
        if point_name is not None:
            point_names.add(point_name)


def retrieve_points_used_to_locate_ad_in_item18(data):
    domestic_departure = data["domestic_departure"]
    domestic_destination = data["domestic_destination"]

    mentioned_points_as_ad = set()

    if domestic_departure and data["departure_ad"] in ("ZZZZ", "AFIL"):
        # Possible use of Point or BearingDistance in item 18 for DEP/
        retrieve_point_name_and_add_to_set(mentioned_points_as_ad, data["dep"])

    if domestic_destination and data["destination_ad"] == "ZZZZ":
        # Possible use of Point or BearingDistance in item 18 for DEST/
        retrieve_point_name_and_add_to_set(mentioned_points_as_ad, data["dest"])

    if (
        domestic_departure
        and domestic_destination
        and (data.get("alt_ad_1", None) == "ZZZZ" or data.get("alt_ad_2", None) == "ZZZZ")
    ):
        # Possible use of Point or BearingDistance in item 18 for keys below
        for key in ("altn", "ralt", "talt"):
            if key in data:
                retrieve_point_name_and_add_to_set(mentioned_points_as_ad, data[key])
    return mentioned_points_as_ad


def retrieve_point_name_from_fpl_route_section(
    fpl_route: list[dict[str, str]], departure: str, destination: str
) -> set[str]:
    points_mentioned_in_route = set()
    for route_section in fpl_route:
        for point in (route_section["from"], route_section["to"]):
            # Since data["departure_ad"], data["destination_ad"] included in section of data["route"]
            if point not in (departure, destination):
                retrieve_point_name_and_add_to_set(points_mentioned_in_route, point)
    return points_mentioned_in_route


def check_points_exists(
    points: set[str], existing_points: dict[str, tuple[Point, QuerySet[str]]], route, err
):
    for point_name in points:
        point_data = existing_points.get(point_name, None)
        if point_data is None:
            err["logical_error"].append(errors.POINT_DOES_NOT_EXIST.format(point_name))
            for section in route:
                if point_name in section["from"] or point_name in section["to"]:
                    section["nonessential"] = True


def route_analyzer(fpl: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]):
    """Analyzes the flight-planned route.

    The flight-planned route consists of points and routes (and speed/level changes, etc.).
    - There are the following Queries in this function:
        1. Points: validate mentioned points existence
            1.1. Prefetch FIRs to check intersection of points FIRs.
        2. FIRs: fetching neighbor FIRs
            2.1. Prefetch boundary points to limit route to the portion using common boundaries.
        3. RouteSection: validate route-section adherence & limiting route to boundaries if required.
        4. RouteScheme: validate route-scheme (TOS) adherence
    """

    domestic_departure = fpl["domestic_departure"]
    domestic_destination = fpl["domestic_destination"]

    is_nondomestic = not domestic_departure or not domestic_destination

    if is_nondomestic and not eet_is_correct(fpl, err):
        # without correct EET it's impossible to detect route section withing our FIR
        return

    # * Step 1.1. Normalize the route
    points_mentioned_in_route = retrieve_point_name_from_fpl_route_section(
        fpl["route"], fpl["departure_ad"], fpl["destination_ad"]
    )

    # In addition to points mentioned in the route section, there might be some points in item18 of the FPL
    points_used_to_locate_ads_in_item18 = retrieve_points_used_to_locate_ad_in_item18(fpl)

    all_existing_points: dict[str, tuple[Point, QuerySet[str]]] = {
        point.indicator: (point, set(fir.indicator for fir in point.fir.all()))
        for point in Point.objects.filter(
            indicator__in=(
                *points_mentioned_in_route,
                *points_used_to_locate_ads_in_item18,
            )
        ).prefetch_related("fir")
    }

    # using copy.deepcopy to avoid unexpected behaviors due to mutability of lists and dicts in python
    route_portion_to_be_checked, existing_sections_dict = normalize_route_portions(
        fpl, all_existing_points, copy.deepcopy(fpl["route"]), err
    )

    if not route_portion_to_be_checked:
        return

    # * Step 1.2. Check existence of points within our FIR
    fpl_points_in_route_portion_within_our_fir = retrieve_point_name_from_fpl_route_section(
        route_portion_to_be_checked, fpl["departure_ad"], fpl["destination_ad"]
    )

    # if is_nondomestic entry & exit points are obtained from database but are not in all_existing_points
    if not domestic_departure:
        fpl_points_in_route_portion_within_our_fir.discard(route_portion_to_be_checked[0]["from"])
    if not domestic_destination:
        fpl_points_in_route_portion_within_our_fir.discard(route_portion_to_be_checked[-1]["to"])

    for points_list in (fpl_points_in_route_portion_within_our_fir, points_used_to_locate_ads_in_item18):
        check_points_exists(points_list, all_existing_points, route_portion_to_be_checked, err)

    # * Step 1.2. Check existence of routes within our FIR
    fpl_route_sections = [
        route_section
        for route_section in route_portion_to_be_checked
        if "nonessential" not in route_section or (route_section["via"] not in ("", "DCT"))
    ]

    fpl_mentioned_routes = set(section["via"] for section in fpl_route_sections)

    existing_routes = set(tp[0] for tp in existing_sections_dict)
    for mentioned_route in fpl_mentioned_routes:
        if mentioned_route not in existing_routes:
            err["logical_error"].append(errors.ROUTE_DOES_NOT_EXIST.format(mentioned_route))

    ...
    # * Step 2.2. Check route-scheme (TOS) adherence
    ...

    # * Step 2.3. Check route section adherence
    # 1. A section from filled flightplan may encompasses more than one database route-section. (2 below)
    fpl_section_and_its_nested_real_sections = list()
    for fpl_route_section in fpl_route_sections:
        try:
            real_sections = find_all_nested_real_sections(fpl_route_section, existing_sections_dict)
        except ValidationError as exp:
            err["logical_error"].append(exp.message)
        else:
            fpl_section_and_its_nested_real_sections.append((fpl_route_section, real_sections))

    for fpl_route_section, real_sections in fpl_section_and_its_nested_real_sections:
        # 2. loop through database route-sections encompassed by filled flightplan route-section
        for section in real_sections:
            # section = (route_name, p1_name, p2_name)
            db_section = existing_sections_dict[section]
            validate_fpl_route_section(fpl_route_section, db_section, fpl, err)
