"""Points Related Checks Module
    this module contains about:
        🗸 DEP, DEST and ALTN Reference Points existence
        🗸 Points existence
        🗸 Points active/us
        🗸 Determine entry/exit point(s) if required
        🗸 Determine entry/exit route-section(s) if required

    there are some codes related to determination of the entrance route section
    which are mostly part of route checks but since those code are based on points
    the code is included in this module, in future may find another solution and refactor the code
"""
import re
from typing import Union

from django.conf import settings
from django.db.models import Q

from apps.general.models import FIR
from apps.points.models import Point
from apps.routes.models import Route
from apps.utils.regex_patterns import LOCATION, POINT


def _retrieve_point_name_and_add_to_dict(dct: dict, key: str, value: str):
    matched = re.match(LOCATION, value) or re.match(POINT, value)
    if matched is not None:
        point_name = matched.groupdict().get("point", matched.groupdict().get("ref_point", None))
        # if SIG_POINT is not a BEARING_DISTANCE then there's no ref_point and point_name is None
        if point_name is not None:
            dct[key] = point_name


def points_checks(data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]):
    point_names_to_check = dict()
    domestic_departure = data["domestic_departure"]
    domestic_destination = data["domestic_destination"]

    if domestic_departure and data["departure_ad"] in ("ZZZZ", "AFIL"):
        _retrieve_point_name_and_add_to_dict(point_names_to_check, f"ITEM18 DEP/{data['dep']}", data["dep"])

    if domestic_destination and data["destination_ad"] == "ZZZZ":
        _retrieve_point_name_and_add_to_dict(
            point_names_to_check, f"ITEM18 DEST/{data['dest']}", data["dest"]
        )

    if (
        domestic_departure
        and domestic_destination
        and (data["alt_ad_1"] == "ZZZZ" or data["alt_ad_2"] == "ZZZZ")
    ):
        for key in ("altn", "ralt", "talt"):
            if key in data:
                _retrieve_point_name_and_add_to_dict(
                    point_names_to_check, f"ITEM18 {key.upper()}/{data[key]}", data[key]
                )

    # checks related to route
    row_route = data["route"][1:] if data["sid"] else data["route"]
    row_route = row_route[:-1] if data["star"] else row_route

    for section in row_route:
        for point_name in (section["from"], section["to"]):
            _retrieve_point_name_and_add_to_dict(point_names_to_check, point_name, point_name)

    existing_points = Point.objects.filter(name__in=point_names_to_check.values()).prefetch_related("fir")
    point_objects = {
        point.name: point for point in existing_points
    }  # Useing hash-map to avoid multiple db query in loop
    for msg, point_name in point_names_to_check.items():
        point_obj = point_objects.get(point_name)
        if point_obj is None:
            err["logical_error"].append(f"{msg if 'ITEM18' in msg else ''}Point {point_name} does not exist.")
            for section in row_route:
                if point_name in (section["from"], section["to"]):
                    section["needs_check"] = False
                if msg in (section["from"], section["to"]):
                    # Except for Ad checks, msg is the actual point referenced in the fpl so this "if" should be here.
                    section["needs_check"] = False
        elif not point_obj.is_active:
            err["logical_error"].append(f"{msg if 'ITEM18' in msg else ''}Point {point_name} is not active.")

    # NOTE: Determaine the route portion that is inside the FIR and needs to be scrutinized
    # if domestic_departure and domestic_destination -> hole route needs to checked
    # else either of Entry, Exit point or both points and the route portion in between, must be determined.

    entered, exited = domestic_departure, domestic_destination

    # TODO: There might be usecase for after_entry_point & before_exit_point to find relevant points some day
    entry_point = before_entry_point = after_entry_point = None
    exit_point = before_exit_point = after_exit_point = None

    for point_obj in existing_points:
        if not entered:
            if point_obj.fir.filter(indicator=settings.FIR_INDICATOR).exists():
                entered, after_entry_point = True, point_obj
                if point_obj.is_fir_boundary:
                    entry_point = point_obj
            else:
                before_entry_point = point_obj

        if not exited:
            if point_obj.fir.filter(~Q(indicator=settings.FIR_INDICATOR)).exists():
                exited, after_exit_point = True, point_obj
                if point_obj.is_fir_boundary:
                    exit_point = point_obj
            else:
                before_exit_point = point_obj

    if not (entered and exited):
        if not data["eet"]:
            err["logical_error"].append("ITEM18 EET/ is not included.")
        elif settings.FIR_INDICATOR not in data["eet"]:
            err["logical_error"].append(
                f"If overflight for {settings.FIR_INDICATOR}, EET/ doesn't mention it."
            )

    if entry_point:
        row_entry_section = [section for section in row_route if section["from"] == entry_point.name].pop()
        row_route = row_route[row_route.index(row_entry_section) :]
    if exit_point:
        row_exit_section = [section for section in row_route if section["to"] == exit_point.name].pop()
        row_route = row_route[: row_route.index(row_exit_section) + 1]

    # Update the data["route"] so in the route cheking data["route"] is limit to the required portion
    # There's one more time this line is repeated Don't remove either of these
    data["route"] = row_route

    if not domestic_departure and entry_point is None:
        # Must determine the entry point
        if before_entry_point is None:
            err["logical_error"].append("Entry point cannot be determind - Unknown point from perv FIR.")
            return

        previous_firs = before_entry_point.fir.filter(~Q(indicator=settings.FIR_INDICATOR))
        if settings.FIR_INDICATOR in data["eet"]:
            previous_firs_eets = data["eet"].split(settings.FIR_INDICATOR)[0]
            previous_fir_by_eet = previous_firs_eets.split()[-1][:4]
            previous_fir = previous_firs.filter(indicator=previous_fir_by_eet).first()
            if previous_fir is None:
                previous_fir = FIR.objects.filter(indicator=previous_fir_by_eet).first()

        elif previous_firs.count() == 1:
            previous_fir = previous_firs.first()

        if previous_fir is None:
            err["logical_error"].append("Entry point cannot be determind - Unknown perv FIR.")
            return

        previous_fir_boundary_points = previous_fir.points.filter(is_boundary_point=True)

        entry_route, row_entry_section = None, None
        for section in row_route:
            if section["from"] == before_entry_point:
                row_entry_section = section
                entry_route = Route.objects.filter(name=section["via"]).prefetch_related("sections").first()
                break

        if entry_route is None:
            err["logical_error"].append("Entry point cannot be determind - Unknown entry route.")
            return

        route_section = entry_route.sections.filter(
            (
                Q(point1__in=previous_fir_boundary_points)
                & Q(point2__fir__indicator__in=[settings.FIR_INDICATOR])
            )
            | (
                Q(point2__in=previous_fir_boundary_points)
                & Q(point1__fir__indicator__in=[settings.FIR_INDICATOR])
            )
        ).first()

        if route_section is None:
            err["logical_error"].append("Entry point cannot be determind - Entry section not found.")

        for point in (route_section.point1, route_section.point2):
            entry_point = point.fir.filter(indicator=settings.FIR_INDICATOR).first()
            if entry_point is not None:
                data["entry_point"] = entry_point
                data["entrance_section"] = route_section
                row_route = row_route[row_route.index(row_entry_section) :]
                if not entry_point.is_active:
                    err["logical_error"].append(f"Point {entry_point} is not active.")
                break
        else:
            err["logical_error"].append("Entry point cannot be determind.")

    if not domestic_destination and exit_point is None:
        # Must determine exit point
        if after_exit_point is None:
            err["logical_error"].append("Entry point cannot be determind - Unknown point from next FIR.")
            return
        next_fir = None
        next_firs = after_exit_point.fir.filter(~Q(indicator=settings.FIR_INDICATOR))
        if settings.FIR_INDICATOR in data["eet"]:
            next_firs_eets = data["eet"].split(settings.FIR_INDICATOR)[1]
            # NOTE: EET/UBBB0100 OIIX0144 OPKC0330 -> split(OIIX)[1] => 0144 OPKC0330
            next_fir_by_eet = next_firs_eets.split()[1][:4]
            next_fir = next_firs.filter(indicator=next_fir_by_eet).first()
            if next_fir is None:
                next_fir = FIR.objects.filter(indicator=next_fir_by_eet).first()

        elif next_firs.count() == 1:
            next_fir = next_firs.first()

        if next_fir is None:
            err["logical_error"].append("Entry point cannot be determind - Unknown next FIR.")
            return

        next_fir_boundary_points = next_fir.points.filter(is_boundary_point=True)

        exit_route, row_exit_section = None, None
        for section in row_route:
            if section["to"] == after_exit_point:
                row_exit_section = section
                exit_route = Route.objects.filter(name=section["via"]).prefetch_related("sections").first()
                break

        if exit_route is None:
            err["logical_error"].append("Exit point cannot be determind - Unknown exit route.")
            return

        route_section = exit_route.sections.filter(
            (Q(point1__in=next_fir_boundary_points) & Q(point2__fir__indicator__in=[settings.FIR_INDICATOR]))
            | (
                Q(point2__in=next_fir_boundary_points)
                & Q(point1__fir__indicator__in=[settings.FIR_INDICATOR])
            )
        ).first()

        if route_section is None:
            err["logical_error"].append("Exit point cannot be determind - Exit section not found.")
            return

        for point in (route_section.point1, route_section.point2):
            exit_point = point.fir.filter(indicator=settings.FIR_INDICATOR).first()
            if exit_point is not None:
                data["exit_point"] = exit_point
                data["exit_section"] = route_section
                row_route = row_route[: row_route.index(row_exit_section) + 1]
                if not exit_point.is_active:
                    err["logical_error"].append(f"Point {exit_point} is not active.")
                break
        else:
            err["logical_error"].append("Exit point cannot be determind.")

    # Update the data["route"] so in the route cheking data["route"] is limit to the required portion
    data["route"] = row_route
