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
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db.models import Q

from apps.general.models import FIR
from apps.points.models import Point
from apps.routes.models import RouteSection
from core.analyzers.route_section_valiation import validate_fpl_route_section
from core.utils.regex_patterns import AERODROME, SIG_POINT


def eet_is_correct(data_dict, err_dict: dict[str, list[str]]) -> bool:
    if not data_dict["eet"]:
        err_dict["logical_error"].append("ITEM18 EET/ is not found.")
        return False
    if settings.FIR_INDICATOR not in data_dict["eet"] and not data_dict["domestic_departure"]:
        err_dict["logical_error"].append(f"The EET/ doesn't mention {settings.FIR_INDICATOR}.")
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
        # if SIG_POINT is not a POINT or BEARING_DISTANCE then there's no ref_point so point_name is None
        if point_name is not None:
            dct[point_name] = value


def check_points_exists_and_are_active(points, existing_points, data_dict, err_dict):
    # point_reference_in_fpl = reference for bearing-distance or actual point indicator
    for point_actual_name, point_reference_in_fpl in points.items():
        point_obj = existing_points.get(point_actual_name, None)
        text = point_reference_in_fpl if "ITEM18" in point_reference_in_fpl else ""
        if point_obj is None:
            err_dict["logical_error"].append(f"Point {point_actual_name} does not exist{text}.")
            for route_section in data_dict["route"]:
                if point_reference_in_fpl in (route_section["from"], route_section["to"]):
                    route_section["section_doesnt_need_check"] = True
        elif not point_obj.is_active:
            err_dict["logical_error"].append(f"Point {point_actual_name} is not active{text}.")


def analyse_points_used_to_locate_ad_in_item18(
    data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]
):
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

    existing_mentioned_points_as_ad = {
        point.name: point
        for point in Point.objects.filter(name__in=mentioned_points_as_ad).prefetch_related("fir")
    }

    check_points_exists_and_are_active(mentioned_points_as_ad, existing_mentioned_points_as_ad, data, err)


def check_fir_and_get_its_boundary_points(fir: FIR, err_dict: dict[str, list[str]]):
    if not fir.is_active:
        err_dict["logical_error"].append(f"FIR {fir} is not active (look at EET/).")
        return

    if not fir.is_adjacent:
        err_dict["logical_error"].append(
            f"FIR {fir} is Nonadjacent to {settings.FIR_INDICATOR} (look at EET/)."
        )
        return

    return fir.points.filter(is_fir_boundary=True)


def is_fir_boundary(pair: tuple[str, Point]):
    point_name, point_object = pair
    return point_object.is_fir_boundary is True


def retrieve_point_name_from_route_sections_and_add_to_dict(route, dct, departure_ad, destination_ad):
    for route_section in route:
        for point in (route_section["from"], route_section["to"]):
            # Since data["departure_ad"], data["destination_ad"] included in section of data["route"]
            if point not in (departure_ad, destination_ad):
                retrieve_point_name_and_add_to_dict(dct, point)


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


def found_boundary_point(
    r_section, index, for_next, text, data, existing_sections, neighbor_fir_boundary_points, err
):
    boundary_route = r_section["via"]
    if boundary_route in ("", "DCT"):
        err["logical_error"].append(
            f"{text.lower()} route to {settings.FIR_INDICATOR} can't be DCT or Null/Empty."
        )
    try:
        route_section = existing_sections.get(
            (
                Q(point1__in=neighbor_fir_boundary_points)
                & Q(point2__fir__indicator__in=[settings.FIR_INDICATOR])
            )
            | (
                Q(point2__in=neighbor_fir_boundary_points)
                & Q(point1__fir__indicator__in=[settings.FIR_INDICATOR])
            ),
            route__name=boundary_route,
        )
    except ObjectDoesNotExist:
        err["logical_error"].append(f"No {text.lower()} route/point to {settings.FIR_INDICATOR} determined.")
    except MultipleObjectsReturned:
        err["logical_error"].append(
            f"Multiple {text.lower()} routes/points (route segments) to {settings.FIR_INDICATOR} determined."
        )
    else:
        boundary_point = (
            route_section.point1 if route_section.point1.is_fir_boundary else route_section.point2
        )
        new_section = copy.deepcopy(r_section)
        if not for_next:
            new_section["from"] = boundary_point.name
            data["route"] = [new_section] + data["route"][index + 1 :]
        else:
            new_section["to"] = boundary_point.name
            data["route"] = data["route"][:index] + [new_section]
        return True
    return False


def found_boundary_limit(data, existing_points, existing_sections, err, for_next):
    """Finds and Limits the flight planed route to the boundary of Our FIR
    for_next: bool - is used to slice the EET and control the flow of code
    """
    # * In python booleans are also integers, so it's possible to use them for list slicing
    # sample: EET/XXXX0000 OBBI0140 OIIX0220
    text = "Entry" if not for_next else "Exit"
    to_from = "from" if not for_next else "to"
    b4_bh_boundary_point, neighbor_fir, neighbor_firs_indicators = None, None, None
    eets = data["eet"].split(settings.FIR_INDICATOR)[for_next].strip().split()

    if eets:
        neighbor_firs_indicators = list(map(lambda string: string[:4], eets[for_next:]))
        neighbor_fir_indicator = neighbor_firs_indicators[(not for_next) * -1]
        neighbor_fir = FIR.objects.filter(indicator=neighbor_fir_indicator).prefetch_related("points").first()
    elif not for_next:
        # In case of flights departing from a neighbor FIR they omit the previous FIR in EET, so we check that
        neighbor_fir = (
            FIR.objects.filter(indicator__startswith=data["departure_ad"][:2])
            .prefetch_related("points")
            .first()
        )
        neighbor_firs_indicators = [neighbor_fir.indicator]

    if neighbor_fir is None:
        err["logical_error"].append(
            f"{text} point to {settings.FIR_INDICATOR} is not determined (look at EET/)."
        )
        return

    neighbor_fir_boundary_points = check_fir_and_get_its_boundary_points(neighbor_fir, err)

    # Iteration over existing_points will eventually give us a point that is located within next firs
    # Reversed iteration over existing_points will eventually give us a point that is located within previous firs
    # that point is the b4_bh_boundary_point and the route which the point is on it is the entry/exit route
    for point_name, point_obj in list(existing_points.items())[:: (not for_next) * -1]:
        try:
            point_obj.fir.get(indicator__in=neighbor_firs_indicators)
        except ObjectDoesNotExist:
            pass
        except MultipleObjectsReturned:
            err["logical_error"].append(
                f"Point {point_name} has more than 2 FIRs. " "Please Inform Administration."
            )
        else:
            # Here is before entry point Or after exit point and this point is out side of our FIR
            b4_bh_boundary_point = point_obj
            break
    else:
        for point_name, point_obj in list(existing_points.items())[:: for_next * -1]:
            try:
                point_obj.fir.get(indicator__in=[settings.FIR_INDICATOR])
            except ObjectDoesNotExist:
                pass
            except MultipleObjectsReturned:
                err["logical_error"].append(
                    f"Point {point_name} has more than 2 FIRs. " "Please Inform Administration."
                )
            else:
                # Here is before exit point Or after entry point and this point is inside our FIR
                b4_bh_boundary_point = point_obj
                to_from = "from" if for_next else "to"
                break

        else:
            err["logical_error"].append(f"{text} point to {settings.FIR_INDICATOR} can not be determined.")
            return

    for index, r_section in enumerate(data["route"]):
        if b4_bh_boundary_point.name in r_section[to_from]:
            if b4_bh_boundary_point.is_fir_boundary:
                # So it says: entry_point is the b4_or_after_boundary_point, entry_section is this section
                data["route"] = data["route"][index:] if not for_next else data["route"][: index + 1]
                return True
            elif found_boundary_point(
                r_section, index, for_next, text, data, existing_sections, neighbor_fir_boundary_points, err
            ):
                return True
    else:
        err["logical_error"].append(
            f"{text} point to {settings.FIR_INDICATOR} can not be determined (second try)."
        )
        return


def route_analyzer(data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]):
    domestic_departure = data["domestic_departure"]
    domestic_destination = data["domestic_destination"]

    if not eet_is_correct(data, err) and (not domestic_departure or not domestic_destination):
        # without correct EET it's not possible to detect route section withing our FIR
        return

    analyse_points_used_to_locate_ad_in_item18(data, err)

    mentioned_points_in_route: OrderedDict[str, str] = OrderedDict()  # {point_name: message}

    retrieve_point_name_from_route_sections_and_add_to_dict(
        data["route"], mentioned_points_in_route, data["departure_ad"], data["destination_ad"]
    )

    existing_mentioned_points: dict[str, Point] = {
        point.name: point
        for point in Point.objects.filter(name__in=mentioned_points_in_route).prefetch_related("fir")
    }

    # To preserve the order of points as they're mentioned in the FPL
    existing_points: OrderedDict[str, Point] = OrderedDict()
    for mentioned_point_in_route in mentioned_points_in_route:
        if mentioned_point_in_route in existing_mentioned_points:
            existing_points[mentioned_point_in_route] = existing_mentioned_points[mentioned_point_in_route]

    check_points_exists_and_are_active(mentioned_points_in_route, existing_mentioned_points, data, err)

    fpl_routes = {
        route_section["via"]
        for route_section in data["route"]
        if "section_doesnt_need_check" not in route_section or (route_section["via"] not in ("", "DCT"))
    }

    existing_sections = RouteSection.objects.filter(route__name__in=fpl_routes).prefetch_related(
        "route", "point1", "point2"
    )

    # 1- If boundary_points are mentioned in the flight plan route, so we can limit the route to that portion
    # 2- Otherwise we have to find the before/after boundary-points
    if not domestic_departure and not found_boundary_limit(
        data, existing_points, existing_sections, err, False
    ):
        return

    if not domestic_destination and not found_boundary_limit(
        data, existing_points, existing_sections, err, True
    ):
        return
    # Here data["route"] must only contain the route portion within our FIR
    # so starting form it's first section to the last one there are some sections that have to be broken to smaller and
    # real-data sections also some sections of the filled data may not need to be checked (invalid point, dct, etc.)

    existing_sections_dict = {
        (sec.route.name, sec.point1.name, sec.point2.name): sec for sec in existing_sections
    }

    fpl_routes = {
        route_section
        for route_section in data["route"]
        if "section_doesnt_need_check" not in route_section or (route_section["via"] not in ("", "DCT"))
    }

    fpl_section_and_its_nested_real_sections = {}
    for fpl_route_section in fpl_routes:
        try:
            real_sections = find_all_nested_real_sections(fpl_route_section, existing_sections_dict)
        except ValidationError as e:
            err["logical_error"].append(e.message)
        else:
            fpl_section_and_its_nested_real_sections[fpl_route_section] = real_sections

    for fpl_route_section, real_sections in fpl_section_and_its_nested_real_sections.items():
        for section in real_sections:
            # section = (route_name, p1_name, p2_name)
            db_section = existing_sections_dict[section]
            validate_fpl_route_section(fpl_route_section, db_section, data, err)
