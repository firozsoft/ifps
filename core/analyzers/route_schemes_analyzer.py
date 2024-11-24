# ruff:noqa
# This module is intended to contain analysis for route-scheme(TOS) adherence
def route_scheme_analyzer(fpl, route: list[dict], errors: dict[str, list[str | None]]):
    if not (fpl and route):
        return
    from_fir = route[0].get("from-fir")
    to_fir = route[-1].get("to-fir")

    fpl_route = " ".join(f"{portion['from']} {portion['via']}" for portion in route) + route[-1].get("to")
