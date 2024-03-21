from django.db.models import QuerySet

from apps.general.models.base import FIR


def successfully_limited_route_portion(
    our_fir: FIR,
    neighbor_fir: FIR,
    fpl_route: list[dict],
    existing_points: dict,
    entry_or_exit: str,
    eet: str,
    err: dict,
):
    """Limits the flight-planned route to the portion within our FIR.

    Based on looking for Entry/Exit point and with the help of EET iterate through the filled route and:
        - Departure within other FIRs:
            - locate first point that is not within Previous FIRs (either inside our FIR or following FIRs).
        - Destination within other FIRs:
            - locate last point that is not within Next FIRs (either inside our FIR or FIRs before).

        - the route of the section contins that point as `to_or_from` is the entry/exit route to our FIR.
        - using common_boundaries with neighbor FIR and that route find the boundary point (entry/exit point).
        - create a route section that contains that boundary point, plus data of that fpl route section.
        - update fpl route section to either start or end with that new generated section.

    - NOTE IndexError: for non local departure, if start with a route before our FIR to a point inside or
        after our FIR:
            - Entry fpl route section is the current section containing that point.
            - using neighbor_fir common_boundaries and the route of this section, find boundary point.
            - set that boundary point as fpl_route[0]["from"]

    - NOTE: 'fpl_route' and its sections are mutable, so changes made to them will persist globally.

    """

    if neighbor_fir is None:
        err["logical_error"].append(
            f"{entry_or_exit} point to {our_fir} can not be determined using adjacent FIR(1)."
        )
        return False

    common_boundaries: QuerySet = our_fir.get_common_boundary_points(neighbor_fir)

    if not common_boundaries.exists():
        err["logical_error"].append(
            f"Either {neighbor_fir} is Nonadjacent to {our_fir} or Boundary points can not be determined."
        )
        return False

    # for entry point to_or_from must be "from", for exit point it must be "to"
    to_or_from = "to" if entry_or_exit == "Exit" else "from"

    fir_indicators = list(map(lambda string: string.strip()[:4], eet.split()))
    our_fir_indicator_index = fir_indicators.index(our_fir.indicator)

    previous_firs_indicators = set(fir_indicators[:our_fir_indicator_index])
    next_firs_indicators = set(fir_indicators[our_fir_indicator_index + 1 :])

    if entry_or_exit == "Entry":
        # in case of departures from adjacent FIRs they may omit Previous FIR in EET
        previous_firs_indicators.add(neighbor_fir.indicator)

    for index, section in enumerate(fpl_route):
        if point_data := existing_points.get(section[to_or_from], None):
            point_firs = point_data[1]
            """
            - Find boundary_section to then edit it's to/from point and keep in mind it's mutable
            - Find boundary_route to be able to use it in finding boundary_point
            - Delete nonessential portions of fpl_route where exists
            """
            if entry_or_exit == "Entry" and not previous_firs_indicators.intersection(point_firs):
                try:
                    boundary_section, boundary_route = fpl_route[index - 1], fpl_route[index - 1]["via"]
                    if boundary_route in ("", "DCT"):
                        continue
                    fpl_route = fpl_route[index - 1 :]
                    break
                except IndexError:
                    # Incase of departures from adjacent FIRs - No nonessential portions for fpl_route exists
                    boundary_section, boundary_route = section, fpl_route[index]["via"]
                    if boundary_route in ("", "DCT"):
                        continue
                    break

            if entry_or_exit == "Exit" and next_firs_indicators.intersection(point_firs):
                boundary_section, boundary_route = fpl_route[index], fpl_route[index]["via"]
                if boundary_route in ("", "DCT"):
                    continue
                fpl_route = fpl_route[: index + 1]
                break
    else:
        err["logical_error"].append(
            f"{entry_or_exit} point to {our_fir} can not be determined using adjacent FIR(2)."
        )
        return False

    qs1 = common_boundaries.as_p1_route_sections.filter(route__indicator=boundary_route, point2__fir=our_fir)
    qs2 = common_boundaries.as_p2_route_sections.filter(route__indicator=boundary_route, point1__fir=our_fir)
    db_sections = qs1.union(qs2)

    if db_sections.count() != 1:
        err["logical_error"].append(
            f"{entry_or_exit} point to {our_fir} can not be determined using adjacent FIR(3)."
        )
        return False

    db_section = db_sections.first()
    boundary_point = db_section.point1 if db_section.point1.is_fir_boundary else db_section.point2

    # Using the dict/list mutability feature
    boundary_section[to_or_from] = boundary_point
    return True
