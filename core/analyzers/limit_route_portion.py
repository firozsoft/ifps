from django.conf import settings
from django.db.models import Prefetch, Q, QuerySet

from apps.general.models.base import FIR
from apps.points.models import Point
from apps.routes.models import RouteSection
from core.analyzers import error_messages as errors


def get_essential_route_portion(
    our_fir: FIR,
    neighbor_fir: FIR,
    fpl_route: list[dict],
    existing_points: dict[str, tuple[Point, QuerySet[str]]],
    entry_or_exit: str,
    eet: str,
    err: dict,
):
    """Drop nonessential portions of fpl_route where exists

    The idea here is to walk trough the fpl route to reach a point that is not within the FIRs whom's
    indicators are mentioned in EET before our FIR indicator(incoming flights);
    or a point that is whithin (or in common with) the FIRs whom's indicators are mentioned in EET after
    our FIR indicator(for outgoing flights). index of section contaning such a point with regard to the
    incoming/outgoing (or "to"/"from" in section) is where the route portion have to be cutted out.
    """

    if neighbor_fir is None:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_NO_ADJACENT_FIRS.format(entry_or_exit, our_fir)
        )
        return []

    common_boundaries = set(our_fir.boundary_points).intersection(set(neighbor_fir.boundary_points))

    if not common_boundaries:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_NONADJACENT_FIR_OR_NO_BOUNDARY.format(neighbor_fir, our_fir)
        )
        return []

    fir_indicators = list(map(lambda string: string.strip()[:4], eet.split()))
    our_fir_indicator_index = fir_indicators.index(our_fir.indicator)

    previous_firs_indicators = set(fir_indicators[:our_fir_indicator_index])
    next_firs_indicators = set(fir_indicators[our_fir_indicator_index + 1 :])

    if entry_or_exit == "Entry":
        # in case of departures from adjacent FIRs they may omit Previous FIR in EET
        previous_firs_indicators.add(neighbor_fir.indicator)

    for index, section in enumerate(fpl_route):
        if point_data := existing_points.get(section["to"], None):
            point_firs = point_data[1]
            if entry_or_exit == "Entry" and not previous_firs_indicators.intersection(point_firs):
                if fpl_route[index]["via"] in ("", "DCT"):
                    continue
                return fpl_route[index:]

            if entry_or_exit == "Exit" and next_firs_indicators.intersection(point_firs):
                if fpl_route[index]["via"] in ("", "DCT"):
                    continue
                return fpl_route[: index + 1]
    else:
        err["logical_error"].append(errors.BOUNDARY_DETERMINATION_ERROR.format(entry_or_exit, our_fir))
        return []


def set_route_boundaries(
    route_portion_to_be_checked,
    existing_sections_dict,
    neighbor_fir,
    boundary_route_indicator,
    entry_or_exit,
    err,
):
    to_or_from = "from" if entry_or_exit == "Entry" else "to"

    possible_boundary_sections = {
        existing_sections_dict[tp] for tp in existing_sections_dict if tp[0] == boundary_route_indicator
    }

    if not possible_boundary_sections:
        err["logical_error"].append(errors.ROUTE_DOES_NOT_EXISTS.format(boundary_route_indicator))
        return []

    for section in possible_boundary_sections:
        boundary_point = None
        if section.point1.is_fir_boundary:
            boundary_point = section.point1

        elif section.point2.is_fir_boundary:
            boundary_point = section.point2

        if boundary_point in neighbor_fir.boundary_points:
            route_portion_to_be_checked[(to_or_from == "to") * -1][to_or_from] = boundary_point.indicator
            # To provide data for route-scheme checks and avoid extra db querying
            route_portion_to_be_checked[(to_or_from == "to") * -1][
                f"{to_or_from}-fir"
            ] = neighbor_fir.indicator
            return route_portion_to_be_checked
    else:
        err["logical_error"].append(
            errors.BOUNDARY_DETERMINATION_ERROR_FROM_TO_FIR_ON_ROUTE.format(
                entry_or_exit, to_or_from, neighbor_fir, boundary_route_indicator
            )
        )
        return []


def normalize_route_portions(fpl, all_existing_points, route_portion_to_be_checked, err):
    """Drops the unessential portion of flight planned route to our FIR and returns the
    normalized fpl route-sections list along with database route sections instances which are converted to
    dictionary to optimize database querying. Incases of failure to limiting the route the err dict gets
    updated with essential messages and two empty lists gets returned. if flight is domestic so the route gets
    no changes but the database sections will be fetched and returned along the unchanged route.

    - it's designed purposefully to have more python code specially multiple if statements on domestic
    departure/destination but to avoid multiple db hits and using cached data instead.
    """

    domestic_departure = fpl["domestic_departure"]
    domestic_destination = fpl["domestic_destination"]

    # This empty Q gets some filtering conditions if nondomestic otherwise has no effect
    boundary_setcion_filter = Q()

    if not domestic_departure or not domestic_destination:
        # Neighbor FIR and Route of flight to/from that FIR gives us the boundary point to limit route portion
        common_boundaries_of3firs = set()
        previous_fir_indicator_2letters, next_fir_indicator_2letters = None, None
        our_fir_indicator_2letters = settings.FIR_INDICATOR[:2]

        if not domestic_departure:
            eets = fpl["eet"].split(settings.FIR_INDICATOR)
            try:
                previous_fir_indicator_2letters = eets[0].strip().split()[-1].strip()[:2]
            except IndexError:
                previous_fir_indicator_2letters = fpl["departure_ad"][:2]

        if not domestic_destination:
            eets = fpl["eet"].split(settings.FIR_INDICATOR)
            try:
                next_fir_indicator_2letters = eets[1].strip().split()[1].strip()[:2]
            except IndexError:
                next_fir_indicator_2letters = "XQ"  # NOTE: FIR indicators can't be started with I,J,X,Q.

        firs_and_their_boundary_points = FIR.objects.filter(
            Q(indicator__startswith=previous_fir_indicator_2letters)
            | Q(indicator__startswith=our_fir_indicator_2letters)
            | Q(indicator__startswith=next_fir_indicator_2letters)
        ).prefetch_related(
            Prefetch(
                "points",
                queryset=Point.objects.filter(is_fir_boundary=True),
                to_attr="boundary_points",
            ),
        )

        FIRs = {fir.indicator[:2]: fir for fir in firs_and_their_boundary_points}

        for _, fir in FIRs.items():
            if not fir.is_active:
                err["logical_error"].append(errors.FIR_IS_NOT_ACTIVE.format(fir))

        our_fir = FIRs.get(our_fir_indicator_2letters, None)
        previous_fir = FIRs.get(previous_fir_indicator_2letters, None)
        next_fir = FIRs.get(next_fir_indicator_2letters, None)

        if not domestic_departure:
            route_portion_to_be_checked = get_essential_route_portion(
                our_fir,
                previous_fir,
                route_portion_to_be_checked,
                all_existing_points,
                "Entry",
                fpl["eet"],
                err,
            )
            if not route_portion_to_be_checked:
                # Without knowing entry point it's impossible to determine exit point.
                return [], []

            common_boundaries_of3firs = set(our_fir.boundary_points).intersection(
                set(previous_fir.boundary_points)
            )

        if not domestic_destination:
            route_portion_to_be_checked = get_essential_route_portion(
                our_fir,
                next_fir,
                route_portion_to_be_checked,
                all_existing_points,
                "Exit",
                fpl["eet"],
                err,
            )
            if not route_portion_to_be_checked:
                # Without knowing entry point it's impossible to determine exit point.
                return [], []

            common_boundaries_of3firs = common_boundaries_of3firs.union(
                set(our_fir.boundary_points).intersection(set(next_fir.boundary_points))
            )

        entry_route_indicator = route_portion_to_be_checked[0]["via"]
        exit_route_indicator = route_portion_to_be_checked[-1]["via"]
        boundary_setcion_filter = Q(route__indicator__in=(entry_route_indicator, exit_route_indicator)) & (
            Q(
                point1__in=common_boundaries_of3firs,
                point2__fir=our_fir,
            )
            | Q(
                point2__in=common_boundaries_of3firs,
                point1__fir=our_fir,
            )
        )

    # up to here route_portion_to_be_checked only contains the routes which are crossing/within our FIR
    fpl_mentioned_routes = set(
        section["via"]
        for section in route_portion_to_be_checked
        if "nonessential" not in section or (section["via"] not in ("", "DCT"))
    )

    existing_sections = (
        RouteSection.objects.filter(Q(route__indicator__in=fpl_mentioned_routes) | (boundary_setcion_filter))
        .distinct()
        .select_related("route", "point1", "point2")
    )

    existing_sections_dict = {
        (sec.route.indicator, sec.point1.indicator, sec.point2.indicator): sec for sec in existing_sections
    }

    if not domestic_departure:
        route_portion_to_be_checked = set_route_boundaries(
            route_portion_to_be_checked,
            existing_sections_dict,
            previous_fir,
            entry_route_indicator,
            "Entry",
            err,
        )
        if not route_portion_to_be_checked:
            return [], []

    if not domestic_destination:
        route_portion_to_be_checked = set_route_boundaries(
            route_portion_to_be_checked,
            existing_sections_dict,
            next_fir,
            exit_route_indicator,
            "Exit",
            err,
        )
        if not route_portion_to_be_checked:
            return [], []

    if not existing_sections_dict:
        err["logical_error"].append(errors.ROUTE_PORTION_DETERMINATION_ERROR.format(our_fir))
        return [], []

    return route_portion_to_be_checked, existing_sections_dict
