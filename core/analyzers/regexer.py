import copy
import re
from datetime import datetime
from typing import Union

from core.utils import regex_patterns
from core.utils.patterns import OTHER_INFO_SWITCHES


def _update_segments(segment_list: list[dict[str, str]], to: str):
    """
    Update the segments list by setting the 'to' attribute of the last segment
    and appending a new segment with the given 'to' attribute.

    Args:
        segment_list (list): List of segment dictionaries.
        to (str): Value to set as the 'to' attribute of the last segment and 'from' attribute of the new segment.

    This function updates the segment list by modifying the last segment's 'to' attribute and appending a new segment
    with the given 'to' attribute and empty 'via' attribute, while preserving other attributes.
    """
    # Update the 'to' attribute of the last segment
    segment_list[-1]["to"] = to

    # Create a new segment by deepcopying the last segment and modifying necessary attributes
    new_segment = copy.deepcopy(segment_list[-1])
    new_segment["from"] = to
    new_segment["to"] = ""

    # Append the new segment to the segment list
    segment_list.append(new_segment)


def _check_and_handle_possible_speed_level_change(
    pattern: str,
    matched: re.Match,
    segments: list[dict[str, str]],
):
    """
    Check and handle possible speed and level changes in the flight segments.

    Args:
        pattern (str): Regular expression pattern.
        matched (re.Match): Match object containing the matched groups.
        segments (list): List of flight segments.

    This function checks if the given pattern corresponds to a change in speed and/or level,
    and updates the last flight segment accordingly.
    """
    # Extract matched groups from the regex match
    groups = matched.groupdict()

    # Update speed and level attributes of the last flight segment
    segments[-1]["speed"] = groups.get("speed", segments[-1]["speed"])
    segments[-1]["level"] = groups.get("level", segments[-1]["level"])

    # Update top level attribute for cruise climb pattern
    if pattern == regex_patterns.CRUISE_CLIMB:
        segments[-1]["top_level"] = groups.get("top_level", segments[-1]["top_level"])
    else:
        segments[-1]["top_level"] = segments[-1]["level"]


def _check_item_is_valid_point_with_indicator(
    item: str,
    previous: dict[str, str],
    segments: list[dict[str, str]],
    err: dict,
):
    """
    Check if the item is a valid point with an indicator and update previous accordingly.

    Args:
        item (str): The item to check.
        previous (dict): Previous item information.
        segments (list): List of flight segments.
        err (dict): Dictionary to store error messages.

    This function checks if the given item is a valid point with an indicator, validates its syntax,
    and updates the previous item information accordingly. It also handles possible speed and level changes.
    """
    matched_pattern = None
    for pattern in (regex_patterns.CHANGE_SPEED_LEVEL, regex_patterns.CRUISE_CLIMB, regex_patterns.POINT):
        matched = re.match(pattern, item)
        if matched is not None:
            matched_pattern = pattern
            break
    else:
        err["syntax_error"].append(f"Item {item} (after {previous['item']}) is not valid syntax.")
        return

    point_indicator = matched.groupdict().get("point", None)
    if point_indicator is None:
        err["syntax_error"].append(f"Item {item} must be a valid point indicator, not a location.")
        return

    if previous["type"] == "sid" and previous["item"][:-2] not in (point_indicator, point_indicator[:-1]):
        err["syntax_error"].append(f"Point {item} doesn't match with SID {previous['item']}.")

    # Update previous item information
    previous = {"type": "point", "item": point_indicator}

    # Handle possible speed and level changes
    _check_and_handle_possible_speed_level_change(matched_pattern, matched, segments)

    return previous


def _check_item_is_valid_point_or_location(
    item: str,
    previous: dict[str, str],
    segments: list[dict[str, str]],
    err: dict,
):
    """
    Check if the item is a valid significant point or location and update previous accordingly.

    Args:
        item (str): The item to check.
        previous (dict): Previous item information.
        res (dict): Dictionary to store additional information.
        segments (list): List of flight segments.
        err (dict): Dictionary to store error messages.

    This function checks if the given item is a valid significant point or location,
    validates its syntax, and updates the previous item information accordingly.
    It also handles possible speed and level changes.
    """
    matched_pattern = None
    for pattern in (regex_patterns.CHANGE_SPEED_LEVEL, regex_patterns.CRUISE_CLIMB, regex_patterns.SIG_POINT):
        matched = re.match(pattern, item)
        if matched is not None:
            matched_pattern = pattern
            break
    else:
        err["syntax_error"].append(f"{item} (after {previous['item']}) must be a valid Significant point.")
        return

    location = matched.groupdict().get("location", None)
    if location is not None:
        previous = {"type": "location", "item": location}
        segments[-1]["nonessential"] = True
    else:
        point = matched.groupdict().get("point", None)
        if point is not None:
            previous = {"type": "point", "item": point}

    # Handle possible speed and level changes
    _check_and_handle_possible_speed_level_change(matched_pattern, matched, segments)

    return previous


def _check_item_is_valid_route_or_dct_or_ifr_vfr(
    item: str,
    previous: dict[str, str],
    res: dict,
    segments: list[dict[str, str]],
    err: dict,
):
    """
    Check if the item is a valid route, DCT, or change of flight rule (IFR/VFR) and update previous accordingly.

    Args:
        item (str): The item to check.
        previous (dict): Previous item information.
        res (dict): Dictionary to store additional information.
        segments (list): List of flight segments.
        err (dict): Dictionary to store error messages.

    This function checks if the given item is a valid route, DCT, or change of flight rule (IFR/VFR),
    validates its syntax, and updates the previous item information accordingly.
    """
    matched = re.match(regex_patterns.SID_STAR, item)
    if matched:
        point = matched.groupdict().get("point")
        if point not in (previous["item"], previous["item"][:-1]):
            err["syntax_error"].append(f"Point {previous['item']} doesn't match with STAR {item}.")
        else:
            star = matched.groupdict().get("sid_star")
            previous = {"type": "route", "item": star}
            segments[-1]["via"] = star
            res["star"] = star

    elif matched := re.match(regex_patterns.ROUTE, item):
        route = matched.groupdict().get("route")
        previous = {"type": "route", "item": route}
        segments[-1]["via"] = route

    elif item == "DCT":
        previous = {"type": "dct", "item": "DCT"}
        segments[-1]["via"] = "DCT"
        segments[-1]["nonessential"] = True

    elif item in ("IFR", "VFR") and re.match(regex_patterns.CHANGE_FLT_RULE, f"{previous['item']} {item}"):
        if res["flight_rule"] not in ("Y", "Z"):
            err["syntax_error"].append(
                f"Illegal change of flight rule (after {previous['item']}) initial one was not 'Y' or 'Z'."
            )
        if segments[-1]["flight_rule"] == item[0]:
            err["syntax_error"].append(
                f"{item} (after {previous['item']}) is Incorrect change of flight rule. {item} to {item}."
            )
        else:
            segments[-1]["flight_rule"] = item[0]
    else:
        err["syntax_error"].append(
            f"{item} (after {previous['item']}) must be a Route or DCT or Change of flight rule (IFR/VFR)."
        )
        return

    return previous


def route_regex_parse(
    data: dict[str, str],
    res: dict[str, Union[str, list[dict[str, str]]]],
    err: dict[str, list[str]],
):
    """
    Checks for syntax errors in the route part of an FPL message.

    Args:
        data (dict): The FPL data.
        res (dict): Dictionary to store results.
        err (dict): Dictionary to store error messages.
    """

    # Extract initial speed and level from the route data
    route_items = data["route"].split()
    init_sp_lvl = re.match(regex_patterns.SPEED_LEVEL, route_items[0])
    if init_sp_lvl is not None:
        res["initial_speed"] = init_sp_lvl.groupdict().get("speed")
        res["initial_level"] = init_sp_lvl.groupdict().get("level")
    else:
        err["syntax_error"].append(f"{route_items[0]} must be a valid speed & level.")

    # keep a look at item already checked to be able to expect the nature of next item to be checked
    previous: dict[str, str] = {"type": "", "item": ""}

    # route_items[1] must be DCT, Route or Point
    if route_items[1] == "DCT":
        previous = {"type": "dct", "item": "DCT"}

    elif item := re.match(regex_patterns.ROUTE, route_items[1]):
        previous = {"type": "route", "item": item.groupdict().get("route")}

    elif item := re.match(regex_patterns.SID_STAR, route_items[1]):
        previous = {"type": "sid", "item": item.groupdict().get("sid_star")}
        res["sid"] = item.groupdict().get("sid_star")

    elif item := re.match(regex_patterns.POINT, route_items[1]):
        previous = {"type": "point", "item": item.groupdict().get("point")}

    elif item := re.match(regex_patterns.LOCATION, route_items[1]):
        previous = {"type": "location", "item": item.groupdict().get("location")}

    else:
        err["syntax_error"].append(f"{route_items[1]} must be a valid ATS Route or DCT or an ATS Point")
        return

    # route segments
    segments: list[dict[str, str]] = [
        {
            "from": res["departure_ad"],
            "to": previous["item"] if previous["type"] in ("point", "location") else "",
            "via": previous["item"] if previous["type"] in ("route", "dct", "sid") else "",
            "speed": res["initial_speed"],
            "level": res["initial_level"],
            "top_level": res["initial_level"],
            "flight_rule": "I" if res["flight_rule"] in ("I", "Y") else "V",
        }
    ]

    rest_of_route_items = route_items[2:]
    set_rest_of_route_items = set(rest_of_route_items)

    # Check if flight rule needs to be changed and handle error cases
    needs_change_of_flt_rule = res["flight_rule"] in ("Z", "Y")
    if needs_change_of_flt_rule:
        if res["flight_rule"] == "Z" and "IFR" not in set_rest_of_route_items:
            err["syntax_error"].append(
                f"Flight rule is filled as {res['flight_rule']} but doesn't change (to IFR) in the route."
            )
        if res["flight_rule"] == "Y" and "VFR" not in set_rest_of_route_items:
            err["syntax_error"].append(
                f"Flight rule is filled as {res['flight_rule']} but doesn't change (to VFR) in the route."
            )

    # Process each item in the route
    # previous['type'] == 'route' | 'dct' | 'point' | 'location'
    for item in rest_of_route_items:
        # NOTE: _update_segments must only be called if item is a SIG_POINT not for DCT or ROUTE or IFR/VFR or etc.
        if previous is None:
            return
        if previous["type"] in ("route", "sid"):
            # current item can be a point that has an assigned indicator (point, change speed-level, cruise-climb)
            previous = _check_item_is_valid_point_with_indicator(item, previous, segments, err)
            _update_segments(segments, previous["item"])
        elif previous["type"] == "dct":
            # current item can be a sig-point
            previous = _check_item_is_valid_point_or_location(item, previous, segments, err)
            _update_segments(segments, previous["item"])
        elif previous["type"] == "point":
            # current item can be a route or dct or IFR/VFR
            previous = _check_item_is_valid_route_or_dct_or_ifr_vfr(item, previous, res, segments, err)
        elif previous["type"] == "location":
            # current item can be a location or dct => this means there's no predefined route section used here
            segments[-1]["nonessential"] = True
            if item == "DCT":
                previous = {"type": "dct", "item": "DCT"}
                segments[-1]["via"] = "DCT"
            elif matched := re.match(regex_patterns.LOCATION, item):
                previous = {"type": "location", "item": matched.groupdict().get("location")}
                _update_segments(segments, previous["item"])
            else:
                err["syntax_error"].append(
                    f"{item} (after {previous['item']}) must be a valid Sig. Point or the word DCT."
                )

    # Set the 'to' value for the last segment to the destination aerodrome
    segments[-1]["to"] = res["destination_ad"]

    # Store the route segments in the result dictionary
    res["route"] = segments


def regex_parse(
    row_data: dict[str, str],
) -> tuple[dict[str, Union[str, list[dict[str, str]]]], Union[dict[str, str], None]]:
    """
    Checks for syntax errors and prepares a new dict.

    Args:
        row_data (dict): The flight plan data.

    Returns:
        tuple: A tuple containing parsed data and errors, if any.
    """

    regex_parsed_data = dict()
    errors = None
    err = {"syntax_error": []}

    # Validate call sign
    call_sign = re.match(regex_patterns.AIRCRAFT_IDENTIFICATION, row_data["call_sign"])
    if not call_sign:
        err["syntax_error"].append(f"Invalid call-sign ({row_data['call_sign']}).")
    else:
        regex_parsed_data["call_sign"] = call_sign.group()

    # Validate flight rule/type
    flt_rule_type = re.match(regex_patterns.FLIGHT_RULE_TYPE, row_data["flt_rule_type"])
    if not flt_rule_type:
        err["syntax_error"].append(f"Invalid flight rule/type ({row_data['flt_rule_type']}).")
    else:
        regex_parsed_data.update(flt_rule_type.groupdict())

    # Validate numbers/type/weak
    numbers_type_weak = re.match(regex_patterns.AC_NUMBER_TYPE_WAKE, row_data["numbers_type_weak"])
    if not numbers_type_weak:
        err["syntax_error"].append(f"Invalid numbers/type/weak ({row_data['numbers_type_weak']}).")
    else:
        regex_parsed_data.update(numbers_type_weak.groupdict())

    # Validate equipments/capacities
    equp_cpct = re.match(regex_patterns.EQUIPMENTS_CAPACITIES, row_data["equipments_and_capacities"])
    if not equp_cpct:
        err["syntax_error"].append(
            f"Invalid equipments/capacities ({row_data['equipments_and_capacities']})."
        )
    else:
        regex_parsed_data.update(equp_cpct.groupdict())

    # Validate departure aerodrome and time
    dep_ad_time = re.match(regex_patterns.DEPARTURE_AD_TIME, row_data["dep_ad_time"])
    if not dep_ad_time:
        err["syntax_error"].append(f"Invalid departure aerodrome or time ({row_data['dep_ad_time']}).")
    else:
        regex_parsed_data.update(dep_ad_time.groupdict())

    # Validate destination aerodrome, teet, and alternates
    dest_teet_alt = re.match(regex_patterns.DEST_AD_TEET_ALTS, row_data["dest_teet_alts"])
    if not dest_teet_alt:
        err["syntax_error"].append(
            f"Invalid destination aerodrome or time or alternates ({row_data['dest_teet_alts']})."
        )
    else:
        regex_parsed_data.update(dest_teet_alt.groupdict())

    # Parse Other Information
    other_info: list[str] = row_data["others"].split()
    last_switch_index = 0
    for item in other_info[:]:
        if "/" not in item:
            other_info[last_switch_index] += " " + item
            other_info.remove(item)
        else:
            last_switch_index = other_info.index(item)

    for item in other_info[:]:
        for key, pattern in OTHER_INFO_SWITCHES.items():
            if item.startswith(f"{key}/"):
                matched = re.match(pattern, item)
                if matched is not None:
                    regex_parsed_data.update(matched.groupdict())
                else:
                    err["syntax_error"].append(f"Invalid {item} in ITEM18 (Other information).")
                break
        else:
            err["syntax_error"].append(f"{item} is not valid syntax for ITEM18 (Other information).")

    if regex_parsed_data["departure_ad"] in ("ZZZZ", "AFIL"):
        if "dep" not in regex_parsed_data:
            err["syntax_error"].append(
                "DEP is not defined and missing DEP/ switch in ITEM18 (Other information)."
            )
        elif not re.match(regex_patterns.LOCATION, regex_parsed_data["dep"]):
            err["syntax_error"].append(
                f"DEP/ in ITEM18({regex_parsed_data['dep']}) is not a valid Point/Coordinate/BearingDistance."
            )
    elif "dep" in regex_parsed_data:
        err["syntax_error"].append(
            "There must be only one of departure Ad. or DEP/ switch in ITEM18 (Other information)."
        )

    if regex_parsed_data["destination_ad"] == "ZZZZ":
        if "dest" not in regex_parsed_data:
            err["syntax_error"].append(
                "DEST is not defined and missing DEST/ switch in ITEM18 (Other information)."
            )
        elif not re.match(regex_patterns.LOCATION, regex_parsed_data["dest"]):
            err["syntax_error"].append(
                f"DEST/ in ITEM18({regex_parsed_data['dest']}) is not a valid Point/Coordinate/BearingDistance."
            )
    elif "dest" in regex_parsed_data:
        err["syntax_error"].append(
            "There must be only one of destination Ad. or DEST/ switch in ITEM18 (Other information)."
        )

    if regex_parsed_data["alt_ad_1"] == "ZZZZ" or regex_parsed_data["alt_ad_2"] == "ZZZZ":
        if "altn" not in regex_parsed_data:
            err["syntax_error"].append(
                "ALTN is not defined and missing ALTN/ switch in ITEM18 (Other information)."
            )
        elif not re.match(regex_patterns.LOCATION, regex_parsed_data["dest"]):
            err["syntax_error"].append(
                f"ALTN/ in ITEM18({regex_parsed_data['dest']}) is not a valid point or coordinate (7 or 11 characters) or bearing-distance."
            )

    if "dof" not in regex_parsed_data:
        err["syntax_error"].append("Missing DOF/ switch in ITEM18.")
    else:
        try:
            datetime.strptime(regex_parsed_data[key.lower()], "%y%m%d")
        except ValueError:
            err["syntax_error"].append(f"DOF ({regex_parsed_data[key.lower()]}) is not valid (YYMMDD).")

    # Parse Route
    route_regex_parse(row_data, regex_parsed_data, err)

    if err["syntax_error"]:
        errors = {f"{inx}": err for inx, err in enumerate(err["syntax_error"])}
    return regex_parsed_data, errors
