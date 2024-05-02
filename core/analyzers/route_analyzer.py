"""Route Item Related Checks Module.

This module handles the following tasks related to route items:
    🗸 Determine the portion of the route that needs to be checked.
    🗸 Check existence and status (active/inactive) of routes/points.
    🗸 Correlate routes and points.
    🗸 Validate adherence to route sections.
    🗸 Validate adherence to route schemes.

There are four possible flight situations to consider:
   1. Domestic Flight: Both departure and destination are within our FIR.
   2. Domestic Departure (domestic_dep): Only the departure is inside our FIR.
   3. Domestic Destination (domestic_dest): Only the destination is inside our FIR.
   4. Overflight: Neither departure nor destination is inside our FIR.

For flights conducting international operations, EET (Estimated Elapsed Time) in item 18 of the flight plan
is mandatory. By examining previous or next FIRs based on EET relative to our FIR, we can determine
the entry and exit route/point of the flight.

NOTE: If a flight departs from an adjacent FIR, according to the EET, it should start within our FIR.
The previous FIR can be determined using the first two letters of the departure Aerodrome.
"""

import copy
import re

import networkx as nx
from django.conf import settings
from django.core.exceptions import ValidationError

from core.analyzers.route_normalizer import normalizer
from core.analyzers.route_sections_analyzer import validate_fpl_route_section
from core.utils import error_messages as errors
from core.utils.patterns import AERODROME, SIG_POINT


def find_all_nested_real_sections(fpl_route_section: dict[str, str], db_sections: tuple[str, str, str]):
    route, start_point, end_point = (
        fpl_route_section["via"],
        fpl_route_section["from"],
        fpl_route_section["to"],
    )

    db_route_sections = {tp for tp in db_sections if tp[0] == route}

    # Create an undirected graph
    graph = nx.Graph()

    # Add edges to the graph representing route sections
    for tp in db_route_sections:
        graph.add_edge(tp[1], tp[2], route=tp[0])

    try:
        # Use shortest_path to find the path
        path = nx.shortest_path(graph, source=start_point, target=end_point)

    except nx.NetworkXException:
        raise ValidationError(errors.PATH_NOT_FOUND.format(start_point, end_point, route)) from None

    # Filter out edges to get the actual sections
    return [
        (graph[u][v]["route"], u, v)
        for u, v in zip(path[:-1], path[1:], strict=False)
        if graph.has_edge(u, v)
    ]


def eet_is_correct(data, err: dict[str, list[str]]) -> bool:
    if not data["eet"]:
        err["integrity_error"].append(errors.EET_NOT_FOUND)
        return False
    if settings.FIR_INDICATOR not in data["eet"] and not data["domestic_departure"]:
        err["integrity_error"].append(errors.FIR_NOT_FOUND_IN_EET.format(settings.FIR_INDICATOR))
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
    fpl_route: list[dict[str, str]],
    departure: str,
    destination: str,
) -> set[str]:
    points_mentioned_in_route = set()
    for route_section in fpl_route:
        for point in (route_section["from"], route_section["to"]):
            # Since data["departure_ad"], data["destination_ad"] included in section of data["route"]
            if point not in (departure, destination):
                retrieve_point_name_and_add_to_set(points_mentioned_in_route, point)
    return points_mentioned_in_route


def check_points_exists(points: set[str], existing_points: dict[str, set[str]], route, err):
    for point_name in points:
        if point_name not in existing_points:
            err["integrity_error"].append(errors.POINT_DOES_NOT_EXIST.format(point_name))
            for section in route:
                if point_name in section["from"] or point_name in section["to"]:
                    section["nonessential"] = True


def route_analyzer(fpl: dict[str, bool | str | list[dict[str, str]]], err: dict[str, list[str]]):  # noqa:C901
    """Analyzes the flight-planned route.

    The flight-planned route consists of points and routes (and speed/level changes, etc.).
    - There are the following Queries in this function:
        1. FIRs: Fetch all mentioned FIRs of EET
        1.1. Prefetch all points that are mentioned in fpl route for each FIR (point existence check).
        1.2. Prefetch boundary points of neighbor FIRs to limit route to the portion using common boundaries.
        2. RouteSection: validate route-section adherence & limiting route to boundaries if required.
        3. RouteScheme: validate route-scheme (TOS) adherence.
    """
    domestic_departure = fpl["domestic_departure"]
    domestic_destination = fpl["domestic_destination"]

    is_nondomestic = not domestic_departure or not domestic_destination

    if is_nondomestic and not eet_is_correct(fpl, err):
        # without correct EET it's impossible to detect route section withing our FIR
        return {}, {}, {}

    # * Step 1.1. Normalize the route
    points_mentioned_in_route = retrieve_point_name_from_fpl_route_section(
        fpl["route"],
        fpl["departure_ad"],
        fpl["destination_ad"],
    )

    # In addition to points mentioned in the route section, there might be some points in item18 of the FPL
    points_used_to_locate_ads_in_item18 = retrieve_points_used_to_locate_ad_in_item18(fpl)

    mentioned_points_in_fpl = set(points_mentioned_in_route).union(points_used_to_locate_ads_in_item18)

    # using copy.deepcopy to avoid unexpected behaviors due to mutability of lists and dicts in python
    route_portion_to_be_checked, all_existing_points, all_existing_sections, firs = normalizer(
        fpl,
        mentioned_points_in_fpl,
        copy.deepcopy(fpl["route"]),
        err,
    )

    if not route_portion_to_be_checked:
        return {}, {}, {}

    # * Step 1.2. Check existence of points within our FIR
    fpl_points_in_route_portion_within_our_fir = retrieve_point_name_from_fpl_route_section(
        route_portion_to_be_checked,
        fpl["departure_ad"],
        fpl["destination_ad"],
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

    existing_routes = {tp[0] for tp in all_existing_sections}
    for route_section in fpl_route_sections:
        if route_section["via"] not in existing_routes:
            route_section["nonessential"] = True
            err["integrity_error"].append(errors.ROUTE_DOES_NOT_EXIST.format(route_section["via"]))

    # * Step 2.2. Check route section adherence
    # 1. A section from filled flightplan may encompasses more than one database route-section. (2 below)
    fpl_section_and_its_nested_real_sections = []
    for fpl_route_section in fpl_route_sections:
        try:
            real_sections = find_all_nested_real_sections(fpl_route_section, all_existing_sections)
        except ValidationError as exp:
            err["integrity_error"].append(exp.message)
        else:
            fpl_section_and_its_nested_real_sections.append((fpl_route_section, real_sections))

    for fpl_route_section, real_sections in fpl_section_and_its_nested_real_sections:
        # 2. loop through database route-sections encompassed by filled flightplan route-section
        for section in real_sections:
            # section is equal to (route_name, p1_name, p2_name)
            db_section = all_existing_sections[section]
            validate_fpl_route_section(fpl_route_section, db_section, fpl, err)

    # * Step 2.3. Check route-scheme (TOS) adherence

    return all_existing_points, all_existing_sections, firs
