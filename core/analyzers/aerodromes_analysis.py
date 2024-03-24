"""Aerodromes Related Checks Module
    this module contains about:
        ✓ Aerodromes existence
        ✓ Aerodromes accept the flight regarding the flight Type
        ✓ Aerodromes accept the flight regarding the flight Rule
        ✓ Aerodromes accept the flight regarding the Ad. Internationality
        ✓ Aerodromes operational hours and curfews
        ✓ Aerodromes available upon request
        ✓ SID/STAR
"""

import datetime
import re
from typing import Union

from django.conf import settings
from django.db.models import Prefetch, Q, QuerySet

from apps.aerodromes.models import Aerodrome
from apps.aerodromes.models.curfew import Curfew
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.aerodromes.models.temp_closure import TemporaryClosure
from apps.general.models.aircraft import Aircraft
from apps.routes.models.sid_star import SidStar
from core.utils import regex_patterns


def check_aerodrome_operational_hour(
    aerodrome: Aerodrome,
    flight_datetime: datetime,
    flight_rule: str,
    err: dict[str, list[str]],
):
    # flight_date = flight_datetime.date()
    flight_time = flight_datetime.time()

    today_operational_hours = aerodrome.dailyoperationalhours.first()
    if today_operational_hours is None:
        return

    if flight_rule.upper() == "VFR":
        ad_start, ad_end = today_operational_hours.vfr_start_time, today_operational_hours.vfr_end_time
    else:
        ad_start, ad_end = today_operational_hours.start_time, today_operational_hours.end_time

    if ad_start <= flight_time <= ad_end:
        return

    msg = (
        f"Your departure/arrival time {flight_time} at {aerodrome} is not in it's operational hours "
        f"({ad_start} & {ad_end})."
    )

    if not aerodrome.aur:
        err["logical_error"].append(msg)
    else:
        # TODO: instead of error there should be a RMK message that indicates AUR is coordinated.
        err["logical_error"].append(msg + " But this aerodrome is available upon request.")


def check_aerodrome_temporarily_closure(aerodrome: Aerodrome, err: dict[str, list[str]]):
    for temp_closure in aerodrome.temporaryclosures.all():
        err["logical_error"].append(
            f"{aerodrome} is temporary closed, {temp_closure.start} till {temp_closure.end}."
        )


def check_aerodrome_curfew(aerodrome: Aerodrome, data_sts: str, data_rmk: str, err: dict[str, list[str]]):
    for curfew in aerodrome.curfews.all():
        if not any([True for sts in data_sts if sts in curfew.acceptable_sts]) or not any(
            [True for rmk in curfew.acceptable_rmk if rmk in data_rmk]
        ):
            err["logical_error"].append(f"{aerodrome} curfew time, {curfew.start} till {curfew.end}.")


def check_aerodrome_sid_star(sid_star_name: str, type_: str, aerodrome: Aerodrome, err: dict[str, list[str]]):
    sid_star = aerodrome.sid_stars.first()
    if sid_star is None:
        err["logical_error"].append(f"{type_} {sid_star_name} does not exist.")
        return
    if not sid_star.is_active:
        err["logical_error"].append(f"{type_} {sid_star_name} is not active.")

    if not sid_star.nav_aid.is_active:
        err["logical_error"].append(f"{type_} {sid_star_name}, Nav.Aid {sid_star.nav_aid} is not active.")

    if type_ not in sid_star.type:
        err["logical_error"].append(f"{sid_star_name}({sid_star.type}) can't be used as {type_}.")


def analyse(
    aerodrome: Aerodrome,
    flight_rule: str,
    flight_datetime: datetime,
    aircraft_type: str,
    heliports_acceptable_types: set[str],
    err: dict[str, list[str]],
    data_sts: str,
    data_rmk: str,
):
    check_aerodrome_operational_hour(aerodrome, flight_datetime, flight_rule, err)
    check_aerodrome_temporarily_closure(aerodrome, err)
    check_aerodrome_curfew(aerodrome, data_sts, data_rmk, err)

    if aerodrome.type == "heliport" and aircraft_type not in heliports_acceptable_types:
        err["logical_error"].append(f"{aerodrome} is Heliport and isn't available for {aircraft_type}.")

    if flight_rule not in aerodrome.ifr_vfr:
        err["logical_error"].append(f"{aerodrome} does not accept {flight_rule.upper()}.")


def get_aerodrome_queryset(
    indicators: list[str],
    departure_datetime: datetime,
    est_arr_datetime: datetime,
    est_alt_arr_datetime: datetime,
    sid_star_names: list[str],
) -> QuerySet[Aerodrome]:
    """Fetching Aerodrome and it's related properties at once"""

    dailyoperationalhours_filtered_prefetch = Prefetch(
        "dailyoperationalhours",
        queryset=DailyOperationalHour.objects.filter(
            Q(date=departure_datetime.date())
            | Q(date=est_arr_datetime.date())
            | Q(date=est_alt_arr_datetime.date())
        ),
    )
    temporaryclosures_filtered_prefetch = Prefetch(
        "temporaryclosures",
        queryset=TemporaryClosure.objects.filter(
            Q(start__lte=departure_datetime, end__gte=departure_datetime)
            | Q(start__lte=est_arr_datetime, end__gte=est_arr_datetime)
            | Q(start__lte=est_alt_arr_datetime, end__gte=est_alt_arr_datetime)
        ),
    )
    curfews_filtered_prefetch = Prefetch(
        "curfews",
        queryset=Curfew.objects.filter(
            Q(start__lte=departure_datetime, end__gte=departure_datetime)
            | Q(start__lte=est_arr_datetime, end__gte=est_arr_datetime)
            | Q(start__lte=est_alt_arr_datetime, end__gte=est_alt_arr_datetime)
        ),
    )
    sid_stars_filtered_prefetch = Prefetch("sid_stars", SidStar.objects.filter(indicator__in=sid_star_names))

    aerodromes_qs: QuerySet[Aerodrome] = Aerodrome.objects.filter(indicator__in=indicators).prefetch_related(
        dailyoperationalhours_filtered_prefetch,
        temporaryclosures_filtered_prefetch,
        curfews_filtered_prefetch,
        sid_stars_filtered_prefetch,
    )

    return aerodromes_qs


def aerodromes_analyzer(fpl: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, list[str]]):
    """Checks Related To Aerodromes"""

    fpl["domestic_departure"] = True
    if not fpl["departure_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in fpl.keys() and settings.FIR_INDICATOR in fpl["eet"]
    ):
        fpl["domestic_departure"] = False

    fpl["domestic_destination"] = True
    if not fpl["destination_ad"].startswith(settings.FIR_INDICATOR[:2]) or (
        "eet" in fpl.keys() and len(fpl["eet"].split(settings.FIR_INDICATOR)[1].strip()) > 4
    ):
        fpl["domestic_destination"] = False

    if not all([fpl["departure_ad"], fpl["destination_ad"], fpl["alt_ad_1"]]):
        err["logical_error"].append(
            "The Destination, Departure and at least one Alternate Aerodromes are mandatory."
        )
        # if any of these is not found or active, then the rest of the checks could not be done!
        return

    aircraft_type = fpl["aircraft_type"]
    initial_flight_rule = "ifr" if fpl["flight_rule"] in "IY" else "vfr"
    last_flight_rule = "ifr" if fpl["route"][-1]["flight_rule"] in "IY" else "vfr"

    domestic_departure = fpl["domestic_departure"]
    domestic_destination = fpl["domestic_destination"]

    heliports_acceptable_types = set(
        Aircraft.objects.filter(variant="Helicopter").values_list("type", flat=True)
    )
    heliports_acceptable_types.add("HEL")

    dep_datatime = datetime.datetime.strptime(fpl["dof"] + fpl["eobt"], "%y%m%d%H%M")
    est_arrival_datetime = dep_datatime + datetime.timedelta(
        hours=int(fpl["teet"][:2]), minutes=int(fpl["teet"][2:])
    )

    extra_ad_to_check = dict()
    for key in ("DEP", "DEST", "ALTN", "RALT", "TALT"):
        if key.lower() in fpl and (domestic_departure or domestic_destination):
            item18_ad = re.match(regex_patterns.AERODROME, fpl[key.lower()])
            if item18_ad is not None:
                extra_ad_to_check[key] = item18_ad.groupdict().get("aerodrome")

    indicators_to_fetch = {
        key: fpl[key] for key in ("departure_ad", "destination_ad", "alt_ad_1", "alt_ad_2") if key in fpl
    }

    indicators_to_fetch.update(extra_ad_to_check)

    est_alt_arr_datetime = est_arrival_datetime + datetime.timedelta(minutes=30)

    sid_star_names = [sid_star for sid_star in (fpl.get("star", None), fpl.get("sid", None)) if sid_star]

    exiting_aerodromes: dict[str, Aerodrome] = {
        aerodrome.indicator: aerodrome
        for aerodrome in get_aerodrome_queryset(
            set(indicators_to_fetch.values()),
            dep_datatime,
            est_arrival_datetime,
            est_alt_arr_datetime,
            sid_star_names,
        )
    }

    for indicator in indicators_to_fetch.values():
        if indicator not in exiting_aerodromes:
            err["logical_error"].append(f"{indicator} does not exists.")

        elif not exiting_aerodromes[indicator].is_active:
            err["logical_error"].append(f"{indicator} is not active.")

    analyze_arguments = {
        "aircraft_type": aircraft_type,
        "heliports_acceptable_types": heliports_acceptable_types,
        "err": err,
        "data_sts": fpl.get("sts", []),
        "data_rmk": fpl.get("rmk", []),
    }

    departure_indicator = indicators_to_fetch.pop("departure_ad", None)
    departure_ad = exiting_aerodromes.get(departure_indicator, None)
    if departure_ad is not None:
        analyse(departure_ad, initial_flight_rule, dep_datatime, **analyze_arguments)

        if domestic_departure and fpl.get("sid", None) is not None:
            check_aerodrome_sid_star(fpl["sid"], "SID", departure_ad, err)

        if not domestic_destination and not (departure_ad.is_international and departure_ad.aur):
            err["logical_error"].append(
                f"Departure {departure_ad} is not international neither available upon request."
            )

    destination_indicator = indicators_to_fetch.pop("destination_ad", None)
    destination_ad = exiting_aerodromes.get(destination_indicator, None)
    if destination_ad is not None:
        analyse(destination_ad, last_flight_rule, est_arrival_datetime, **analyze_arguments)

        if domestic_destination and fpl.get("star", None) is not None:
            check_aerodrome_sid_star(fpl["star"], "STAR", destination_ad, err)

        if not domestic_departure and not (destination_ad.is_international and destination_ad.aur):
            # TODO: check if AUR is coordinated
            err["logical_error"].append(
                f"Destination {destination_ad} is not international neither available upon request."
            )

    for indicator in indicators_to_fetch.values():
        aerodrome = exiting_aerodromes.get(indicator, None)
        if aerodrome is not None:
            analyse(aerodrome, last_flight_rule, est_alt_arr_datetime, **analyze_arguments)
