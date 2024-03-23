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

from apps.general.models import FIR
from apps.points.models import Point
from apps.routes.models import RouteSection
from core.analyzers.limit_route_portion import successfully_limited_route_portion
from core.analyzers.route_section_validation import validate_fpl_route_section
from core.utils.regex_patterns import AERODROME, SIG_POINT


def eet_is_correct(data, err: dict[str, list[str]]) -> bool:
    if not data["eet"]:
        err["logical_error"].append("ITEM18 EET/ is not found.")
        return False
    if settings.FIR_INDICATOR not in data["eet"] and not data["domestic_departure"]:
        err["logical_error"].append(f"The EET/ doesn't mention {settings.FIR_INDICATOR}.")
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


def retrieve_point_name_from_fpl_route_section(data):
    points_mentioned_in_route = set()
    for route_section in data["route"]:
        for point in (route_section["from"], route_section["to"]):
            # Since data["departure_ad"], data["destination_ad"] included in section of data["route"]
            if point not in (data["departure_ad"], data["destination_ad"]):
                retrieve_point_name_and_add_to_set(points_mentioned_in_route, point)
    return points_mentioned_in_route


def check_points_exists_and_are_active(
    points: set[str],
    existing_points: dict[str, tuple[Point, QuerySet[str]]],
    data,
    err,
):
    for point_name in points:
        point_data = existing_points.get(point_name, None)
        if point_data is None:
            err["logical_error"].append(f"Point {point_name} does not exist.")
            for route_section in data["route"]:
                if point_name in route_section["from"] or point_name in route_section["to"]:
                    route_section["nonessential"] = True
        elif not point_data[0].is_active:
            err["logical_error"].append(f"Point {point_name} is not active.")


def route_portion_within_our_fir_for_nondomestic_flights(
    data, all_existing_points, route_portion_to_be_checked, err
):
    """Limits flight planned route of nondomestic flights to the portions within our FIR"""
    domestic_departure = data["domestic_departure"]
    domestic_destination = data["domestic_destination"]

    # Neighbor FIR and Route of flight to/from that FIR gives us the boundary point to limit route portion
    previous_fir_indicator = next_fir_indicator = None
    if not domestic_departure:
        eets = data["eet"].split(settings.FIR_INDICATOR)
        try:
            previous_fir_indicator = eets[0].strip().split()[-1].strip()[:4]
        except IndexError:
            previous_fir_indicator = (
                FIR.objects.filter(indicator__startswith=data["departure_ad"][:2])
                .values_list("indicator", flat=True)
                .first()
            )

    if not domestic_destination:
        eets = data["eet"].split(settings.FIR_INDICATOR)
        try:
            next_fir_indicator = eets[1].strip().split()[1].strip()[:4]
        except IndexError:
            next_fir_indicator = None

    FIRs = {
        fir.indicator: fir
        for fir in FIR.objects.filter(
            indicator__in=(previous_fir_indicator, settings.FIR_INDICATOR, next_fir_indicator)
        )
    }

    for _, fir in FIRs.items():
        if not fir.is_active:
            err["logical_error"].append(f"FIR {fir} is not active.")

    our_fir = FIRs.get(settings.FIR_INDICATOR, None)
    previous_fir = FIRs.get(previous_fir_indicator, None)
    next_fir = FIRs.get(next_fir_indicator, None)

    if not domestic_departure:
        route_portion_to_be_checked = successfully_limited_route_portion(
            our_fir, previous_fir, route_portion_to_be_checked, all_existing_points, "Entry", data["eet"], err
        )
        if not route_portion_to_be_checked:
            # Without knowing entry point it's impossible to determine exit point.
            return route_portion_to_be_checked

    if not domestic_destination:
        route_portion_to_be_checked = successfully_limited_route_portion(
            our_fir, next_fir, route_portion_to_be_checked, all_existing_points, "Exit", data["eet"], err
        )
    return route_portion_to_be_checked


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
        raise ValidationError(message=f"No path found between {start_point} and {end_point} through {route}.")

    # Filter out edges to get the actual sections
    return [(G[u][v]["route"], u, v) for u, v in zip(path[:-1], path[1:]) if G.has_edge(u, v)]


def route_analyzer(data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]):
    """Analyzes the flight-planned route.

    The flight-planned route consists of points and routes (and speed/level changes, etc.).
    - In this function, points are used to detect the FIR (Flight Information Region),
    and routes are used to determine the path to another FIR.
    """

    domestic_departure = data["domestic_departure"]
    domestic_destination = data["domestic_destination"]

    is_nondomestic = not domestic_departure or not domestic_destination

    if is_nondomestic and not eet_is_correct(data, err):
        # without correct EET it's impossible to detect route section withing our FIR
        return

    # * Step 1. Check points
    points_mentioned_in_route = retrieve_point_name_from_fpl_route_section(data)

    # In addition to points mentioned in the route section, there might be some points in item18 of the FPL
    points_used_to_locate_ads_in_item18 = retrieve_points_used_to_locate_ad_in_item18(data)

    all_existing_points: dict[str, tuple[Point, QuerySet[str]]] = {
        point.indicator: (point, point.fir.values_list("indicator", flat=True).distinct())
        for point in Point.objects.filter(
            indicator__in=(
                *points_mentioned_in_route,
                *points_used_to_locate_ads_in_item18,
            )
        ).prefetch_related("fir")
    }

    check_points_exists_and_are_active(points_mentioned_in_route, all_existing_points, data, err)
    check_points_exists_and_are_active(points_used_to_locate_ads_in_item18, all_existing_points, data, err)

    # * Step 2. Check routes
    # * Step 2.1. Retrieve/Check route portion within our FIR
    route_portion_to_be_checked = copy.deepcopy(data["route"])

    if is_nondomestic:
        route_portion_to_be_checked = route_portion_within_our_fir_for_nondomestic_flights(
            data, all_existing_points, route_portion_to_be_checked, err
        )

    if not route_portion_to_be_checked:
        return

    fpl_route_sections = [
        route_section
        for route_section in route_portion_to_be_checked
        if "nonessential" not in route_section or (route_section["via"] not in ("", "DCT"))
    ]

    fpl_mentioned_routes = set(section["via"] for section in fpl_route_sections)

    existing_sections = RouteSection.objects.filter(route__indicator__in=fpl_mentioned_routes).select_related(
        "route", "point1", "point2"
    )

    existing_sections_dict = {
        (sec.route.indicator, sec.point1.indicator, sec.point2.indicator): sec for sec in existing_sections
    }

    existing_routes = set(tp[0] for tp in existing_sections_dict)
    for mentioned_route in fpl_mentioned_routes:
        if mentioned_route not in existing_routes:
            err["logical_error"].append(f"Route {mentioned_route} does not exists.")

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
            validate_fpl_route_section(fpl_route_section, db_section, data, err)
