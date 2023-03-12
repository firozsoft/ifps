"""Aerodromes Related Checks Module
    this module contains about:
        ✓ Aerodromes existence
        ✓ Aerodromes accept the flight regarding the flight Type
        ✓ Aerodromes accept the flight regarding the flight Rule
        ✓ Aerodromes operational hours and curfews
        ✓ SID/STAR
"""
import datetime
from typing import Union

from django.conf import settings

from apps.aerodromes.models import (
    Aerodrome,
    Curfew,
    DailyOperationalHour,
    TemporaryClosure,
)
from apps.routes.models import SidStar


def _check_flight_type_acceptable(ard: Aerodrome, ac_type: str, err: dict[str, str]) -> None:
    if ard.type == "heliport" and ac_type not in ["HEL", "B212", "B412"]:
        err[
            "logical_error"
        ] += f"{ard} is HELIPORT and isn't applicable for {ac_type}(\
                                accepted types are HEL, B212 and B412). "


def _check_aerodrome_operational_hours(
    aerodrome: Aerodrome, flight_datetime: datetime, flight_rule: str, err: dict[str, str]
):
    flight_date = flight_datetime.date()
    flight_time = flight_datetime.time()
    try:
        aerodrome_hours = aerodrome.dailyoperationalhour.get(date=flight_date)
    except DailyOperationalHour.DoesNotExist:
        pass
    else:
        aerodrome_start = aerodrome_hours.start_time
        aerodrome_end = aerodrome_hours.end_time
        if flight_rule == "VFR":
            aerodrome_start = aerodrome_hours.vfr_start_time
            aerodrome_end = aerodrome_hours.vfr_end_time
        if flight_time <= aerodrome_start or flight_time >= aerodrome_end:
            err["logical_error"] += (
                f"Your time {flight_time} at {aerodrome} is not in its operational "
                f"hours, between {aerodrome_start} and {aerodrome_end}. "
            )


def _check_aerodrome_temporarily_closure(aerodrome: Aerodrome, flight_datetime: datetime, err: dict[str, str]):
    flight_date = flight_datetime.date()
    flight_time = flight_datetime.time()
    try:
        temp_closure = aerodrome.temporaryclosure.get(
            date=flight_date, start_time__lte=flight_time, end_time__gte=flight_time
        )
    except TemporaryClosure.DoesNotExist:
        pass
    else:
        err["logical_error"] += (
            f"{aerodrome} temporary closure, between {temp_closure.start_time} " f"and {temp_closure.end_time}. "
        )


def _check_aerodrome_curfew(
    aerodrome: Aerodrome,
    flight_datetime: datetime,
    data_sts: str,
    data_rmk: str,
    err: dict[str, str],
):
    flight_date = flight_datetime.date()
    flight_time = flight_datetime.time()
    try:
        curfew = aerodrome.curfew.get(date=flight_date, start_time__lte=flight_time, end_date__gte=flight_time)
    except Curfew.DoesNotExist:
        pass
    else:
        if not any(sts in curfew.acceptable_sts for sts in data_sts) or not any(
            [rmk in data_rmk for rmk in curfew.acceptable_rmk]
        ):
            err["logical_error"] += f"{aerodrome} curfew time, between {curfew.start_time} " f"and {curfew.end_time}. "


def _analyse(
    aerodrome: Aerodrome,
    aircraft_type: str,
    flight_rule: str,
    flight_datetime: datetime,
    err: dict[str, str],
    data_sts: str,
    data_rmk: str,
):
    _check_flight_type_acceptable(aerodrome, aircraft_type, err)

    if flight_rule not in aerodrome.ifr_vfr:
        err["logical_error"] += f"{aerodrome} does not accept {flight_rule.upper()}. "

    _check_aerodrome_operational_hours(aerodrome, flight_datetime, flight_rule, err)
    _check_aerodrome_temporarily_closure(aerodrome, flight_datetime, err)
    _check_aerodrome_curfew(aerodrome, flight_datetime, data_sts, data_rmk, err)


def aerodromes_checks(data: dict[str, Union[bool, str, list[dict[str, str]]]], err: dict[str, str]):
    """Checks Related To Aerodromes"""

    flight_type = data["flight_type"]
    initial_flight_rule = "ifr" if data["flight_rule"] in "IY" else "vfr"
    last_flight_rule = "ifr" if data["route"][-1]["flight_rule"] in "IY" else "vfr"

    dep_datatime = datetime.datetime.strptime(data["dof"] + data["eobt"], "%y%m%d%H%M")
    est_arrival_datetime = dep_datatime + datetime.timedelta(hours=int(data["teet"][:2]), minutes=int(data["teet"][2:]))

    def _get_ad(four_letters: str) -> Union[Aerodrome, None]:
        """getting dep, dest and first alt aerodromes"""
        if four_letters in ("ZZZZ", "AFIL"):
            return None
        if not four_letters[:2] == settings.FIR_FOUR_LETTERS[:2]:
            return None
        try:
            ad_model = Aerodrome.objects.get(four_letters=four_letters).prefetch_related(
                "dailyoperationalhour", "temporaryclosure", "curfew"
            )
        except Aerodrome.DoesNotExist:
            err["logical_error"] += f"{four_letters} does not exist. "
        else:
            if not ad_model.is_active:
                err["logical_error"] += f"{four_letters} is not active. "
            else:
                return ad_model

    if not all([data["departure_ad"], data["destination_ad"], data["alt_ad_1"]]):
        err["logical_error"] += "The Destination, Departure and at least one Alternate are Mandatory. "
        # if any of these is not found or active, then the rest of checks could
        # not be done!
        return
    else:
        departure_ad = _get_ad(data["departure_ad"])
        destination_ad = _get_ad(data["destination_ad"])
        alt_ad_1 = _get_ad(data["alt_ad_1"])
        if data["alt_ad_2"] is not None:
            alt_ad_2 = _get_ad(data["alt_ad_2"])

    if departure_ad is not None:
        _analyse(departure_ad, flight_type, initial_flight_rule, dep_datatime, err, data["sts"], data["rmk"])

    if destination_ad is not None:
        _analyse(destination_ad, flight_type, last_flight_rule, est_arrival_datetime, err, data["sts"], data["rmk"])

    if alt_ad_1 is not None:
        _analyse(alt_ad_1, flight_type, last_flight_rule, est_arrival_datetime, err, data["sts"], data["rmk"])

    def _sid_star_check(sid_star: str, type_: str, ad: Aerodrome) -> None:
        if not (it := SidStar.objects.filter(name=sid_star, aerodrome=ad).select_related("point").first()):
            err["logical_error"] += f"{type_} {sid_star} does not exist. "
        else:
            if not it.is_active:
                err["logical_error"] += f"{type_} {sid_star} is not active. "
            if not it.point.is_active:
                err["logical_error"] += f"Point {it.point} is not active. "
            if type_ not in it.type:
                err["logical_error"] += f"{sid_star}({it.type}) is not of type {type_}. "

    if data["domestic_dep"] is True and data["sid"] is not None:
        _sid_star_check(data["sid"], "SID", departure_ad)
    if data["domestic_dest"] is True and data["star"] is not None:
        _sid_star_check(data["star"], "STAR", destination_ad)
