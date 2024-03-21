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
from collections import OrderedDict
from typing import Union

import networkx as nx
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.general.models import FIR
from apps.points.models import Point
from apps.routes.models import RouteSection
from core.analyzers.limite_route_portion import successfully_limited_route_portion
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


def retrieve_point_name_and_add_to_dict(dct: dict, key: str, value: str = ""):
    value = value or key

    if re.match(AERODROME, key):
        # to ignore aerodromes referenced in item 18 as dep, dest, altn, ralt, talt
        return
    matched = re.match(SIG_POINT, key)
    if matched is not None:
        point_name = matched.groupdict().get("point", matched.groupdict().get("ref_point", None))
        # if SIG_POINT is not a POINT or BEARING_DISTANCE then there's no `point` or `ref_point` so
        # point_name is None
        if point_name is not None:
            dct[point_name] = value


def check_points_exists_and_are_active(
    points: OrderedDict[str, str],
    existing_points: dict[str, tuple[Point, tuple[FIR]]],
    data,
    err,
):
    # point_reference_in_fpl = reference for bearing-distance or actual point indicator
    for point_actual_name, point_reference_in_fpl in points.items():
        point_data = existing_points.get(point_actual_name, None)
        text = point_reference_in_fpl if "ITEM18" in point_reference_in_fpl else ""
        if point_data is None:
            err["logical_error"].append(f"Point {point_actual_name} does not exist{text}.")
            for route_section in data["route"]:
                if point_reference_in_fpl in (route_section["from"], route_section["to"]):
                    route_section["nonessential"] = True
        elif not point_data[0].is_active:
            err["logical_error"].append(f"Point {point_actual_name} is not active{text}.")


def retrieve_points_used_to_locate_ad_in_item18(data):
    domestic_departure = data["domestic_departure"]
    domestic_destination = data["domestic_destination"]

    mentioned_points_as_ad: dict[str, str] = {}  # {point_name: message}

    if domestic_departure and data["departure_ad"] in ("ZZZZ", "AFIL"):
        # Possible use of Point or BearingDistance in item 18 for DEP/
        retrieve_point_name_and_add_to_dict(
            mentioned_points_as_ad, data["dep"], f" (look at ITEM18 DEP/{data['dep']})"
        )

    if domestic_destination and data["destination_ad"] == "ZZZZ":
        # Possible use of Point or BearingDistance in item 18 for DEST/
        retrieve_point_name_and_add_to_dict(
            mentioned_points_as_ad, data["dest"], f" (look at ITEM18 DEST/{data['dest']})"
        )

    if (
        domestic_departure
        and domestic_destination
        and (data["alt_ad_1"] == "ZZZZ" or data["alt_ad_2"] == "ZZZZ")
    ):
        # Possible use of Point or BearingDistance in item 18 for keys below
        for key in ("altn", "ralt", "talt"):
            if key in data:
                retrieve_point_name_and_add_to_dict(
                    mentioned_points_as_ad, data[key], f" (look at ITEM18 {key.upper()}/{data[key]})"
                )
    return mentioned_points_as_ad


def is_fir_boundary(pair: tuple[str, Point]):
    point_name, point_object = pair
    return point_object.is_fir_boundary is True


def retrieve_point_name_from_fpl_route_section(data):
    points_mentioned_in_route: OrderedDict[str, str] = OrderedDict()  # {point_name: message}
    for route_section in data["route"]:
        for point in (route_section["from"], route_section["to"]):
            # Since data["departure_ad"], data["destination_ad"] included in section of data["route"]
            if point not in (data["departure_ad"], data["destination_ad"]):
                retrieve_point_name_and_add_to_dict(points_mentioned_in_route, point)
    return points_mentioned_in_route


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

    except nx.NetworkXNoPath:
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

    eet_is_required = not domestic_departure or not domestic_destination

    if eet_is_required and not eet_is_correct(data, err):
        # without correct EET it's impossible to detect route section withing our FIR
        return

    # * Step 1. Check points
    points_mentioned_in_route = retrieve_point_name_from_fpl_route_section(data)

    # In addition to points mentioned in the route section, there might be some points in item18 of the FPL
    points_used_to_locate_ads_in_item18 = retrieve_points_used_to_locate_ad_in_item18(data, err)

    all_existing_points: dict[str, tuple[Point, set[str]]] = {
        point.indicator: (point, set(point.fir.values_list("indicator", flat=True)))
        for point in Point.objects.filter(
            indicator__in=(
                *points_mentioned_in_route.keys(),
                *points_used_to_locate_ads_in_item18.keys(),
            ).prefetch_related("fir")
        )
    }

    check_points_exists_and_are_active(points_mentioned_in_route, all_existing_points, data, err)
    check_points_exists_and_are_active(points_used_to_locate_ads_in_item18, all_existing_points, data, err)

    # * Step 2. Check routes
    # 1- If boundary_points are mentioned in the flight plan route, so we can limit the route to that portion
    # 2- Otherwise we have to find the before/after boundary-points
    previous_fir_indicator = next_fir_indicator = None
    if not domestic_departure:
        eets = data["eet"].split(settings.FIR_INDICATOR)
        try:
            previous_fir_indicator = eets[0].strip().split()[-1].strip()[4:]
        except IndexError:
            previous_fir = FIR.objects.filter(indicator__startswith=data["departure_ad"][:2]).first()

    if not domestic_destination:
        eets = data["eet"].split(settings.FIR_INDICATOR)
        try:
            next_fir_indicator = eets[1].strip().split()[1].strip()[4:]
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

    route_portion_to_be_checked = copy.deepcopy(data["route"])

    if not domestic_departure and not successfully_limited_route_portion(
        our_fir, previous_fir, route_portion_to_be_checked, all_existing_points, "Entry", data["eet"], err
    ):
        return
    if not domestic_destination and not successfully_limited_route_portion(
        our_fir, next_fir, route_portion_to_be_checked, all_existing_points, "Exit", data["eet"], err
    ):
        return

    # Here route_portion_to_be_checked must only contain the route portion within our FIR
    # also some route-sections of the filled fpl may not need to be checked (due invalid point, dct, etc.)

    fpl_route_sections = {
        route_section
        for route_section in route_portion_to_be_checked
        if "nonessential" not in route_section or (route_section["via"] not in ("", "DCT"))
    }

    existing_sections = RouteSection.objects.filter(
        route__indicator__in=set(section["via"] for section in fpl_route_sections)
    ).select_related("route", "point1", "point2")

    existing_sections_dict = {
        (sec.route.indicator, sec.point1.indicator, sec.point2.indicator): sec for sec in existing_sections
    }

    # 1. A section from filled flight plan may cover more than one route-section from the database, (2 below)
    fpl_section_and_its_nested_real_sections = {}
    for fpl_route_section in fpl_route_sections:
        try:
            real_sections = find_all_nested_real_sections(fpl_route_section, existing_sections_dict)
        except ValidationError as exp:
            err["logical_error"].append(exp.message)
        else:
            fpl_section_and_its_nested_real_sections[fpl_route_section] = real_sections

    for fpl_route_section, real_sections in fpl_section_and_its_nested_real_sections.items():
        # 2. loop through database route-sections covered by filled-fpl route-section
        for section in real_sections:
            # section = (route_name, p1_name, p2_name)
            db_section = existing_sections_dict[section]
            validate_fpl_route_section(fpl_route_section, db_section, data, err)
