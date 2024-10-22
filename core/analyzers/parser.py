# ruff:noqa: DTZ005,DTZ007,C901
"""Methods to parse and validate flight message text.

Checks includes validation of message syntax, flight planning rules regarding the use of specific items
in each part of flight plan.

These checks and validation do not require querying to database
but are rules and regulations regarding the text message.

The separation of these validation checks gives a fast fail return for possible syntax error or violation of
fpl text rules without any db hit, which will be unnecessary in case of any error in text message.
For example when a point or route name is inccorrect there is no need to hit database to check its existence.

This module also generates a parsed version of fpl message as a dict, so this dict will be used for future
analysis and checks regarding each section of a flight plan.
"""

import copy
import datetime as dt
import re

from core.utils import patterns


def _update_segments(segment_list: list[dict[str, str]], to: str) -> None:
    """Update the segments list.

    Sets the 'to' attribute of the last segment and appends a new segment with the given 'to' attribute.

    Args:
    ----
        segment_list (list): List of segment dictionaries.
        to (str): Value to set as the 'to' attribute of the last segment and 'from' attribute of the new segment.

    Returns:
    -------
        None

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
    """Check and handle possible speed and level changes in the flight segments.

    This function checks if the given pattern corresponds to a change in speed and/or level,
    and updates the last flight segment accordingly.

    Args:
    ----
        pattern (str): Regular expression pattern.
        matched (re.Match): Match object containing the matched groups.
        segments (list): List of flight segments.

    Returns:
    -------
        None

    """
    # Extract matched groups from the regex match
    groups = matched.groupdict()

    # Update speed and level attributes of the last flight segment
    segments[-1]["speed"] = groups.get("speed", segments[-1]["speed"])
    segments[-1]["level"] = groups.get("level", segments[-1]["level"])

    # Update top level attribute for cruise climb pattern
    if pattern == patterns.CRUISE_CLIMB:
        segments[-1]["top_level"] = groups.get("top_level", segments[-1]["top_level"])
    else:
        segments[-1]["top_level"] = segments[-1]["level"]


def _check_item_is_valid_point_with_indicator(
    item: str,
    previous: dict[str, str],
    segments: list[dict[str, str]],
    err: dict,
):
    """Check if the item is a valid point with an indicator and update previous accordingly.

    This function checks if the given item is a valid point with an indicator, validates its syntax
    and updates the previous item information accordingly. It also handles possible speed and level changes.

    Args:
    ----
        item (str): The item to check.
        previous (dict): Previous item information.
        segments (list): List of flight segments.
        err (dict): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    matched_pattern = None
    for pattern in (patterns.CHANGE_SPEED_LEVEL, patterns.CRUISE_CLIMB, patterns.POINT):
        matched = re.match(pattern, item)
        if matched is not None:
            matched_pattern = pattern
            break
    else:
        err["syntax_error"].append(f"Item {item} (after {previous['item']}) is not valid syntax.")
        return None

    point_indicator = matched.groupdict().get("point", None)
    if point_indicator is None:
        err["syntax_error"].append(f"Item {item} must be a valid point indicator, not a location.")
        return None

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
    """Check if the item is a valid significant point or location and update previous accordingly.

    This function checks if the given item is a valid significant point or location,
    validates its syntax and updates the previous item information accordingly.
    It also handles possible speed and level changes.

    Args:
    ----
        item (str): The item to check.
        previous (dict): Previous item information.
        res (dict): Dictionary to store additional information.
        segments (list): List of flight segments.
        err (dict): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    matched_pattern = None
    for pattern in (patterns.CHANGE_SPEED_LEVEL, patterns.CRUISE_CLIMB, patterns.SIG_POINT):
        matched = re.match(pattern, item)
        if matched is not None:
            matched_pattern = pattern
            break
    else:
        err["syntax_error"].append(f"{item} (after {previous['item']}) must be a valid Significant point.")
        return None

    point = matched.groupdict().get("point", None)
    if point is not None:
        previous = {"type": "point", "item": point}
    else:
        location = matched.groupdict().get("location", None)
        if location is not None:
            previous = {"type": "location", "item": location}
            segments[-1]["nonessential"] = True
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
    """Check if the item is a valid route, DCT, or change of flight rule (IFR/VFR).

    This function checks if the given item is a valid route, DCT, or change of flight rule (IFR/VFR),
    validates its syntax and updates the previous item information accordingly.

    Args:
    ----
        item (str): The item to check.
        previous (dict): Previous item information.
        res (dict): Dictionary to store additional information.
        segments (list): List of flight segments.
        err (dict): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    matched = re.match(patterns.SID_STAR, item)
    if matched:
        point = matched.groupdict().get("point")
        if point not in (previous["item"], previous["item"][:-1]):
            err["syntax_error"].append(f"Point {previous['item']} doesn't match with STAR {item}.")
        else:
            star = matched.groupdict().get("sid_star")
            previous = {"type": "route", "item": star}
            segments[-1]["via"] = star
            res["star"] = star

    elif matched := re.match(patterns.ROUTE, item):
        route = matched.groupdict().get("route")
        previous = {"type": "route", "item": route}
        segments[-1]["via"] = route

    elif item == "DCT":
        previous = {"type": "dct", "item": "DCT"}
        segments[-1]["via"] = "DCT"
        segments[-1]["nonessential"] = True

    elif item in ("IFR", "VFR") and re.match(patterns.CHANGE_FLT_RULE, f"{previous['item']} {item}"):
        if res["flight_rule"] not in ("Y", "Z"):
            err["syntax_error"].append(
                f"Illegal change of flight rule (after {previous['item']}) initial one was not 'Y' or 'Z'.",
            )
        if segments[-1]["flight_rule"] == item[0]:
            err["syntax_error"].append(
                f"{item} (after {previous['item']}) is Incorrect change of flight rule. {item} to {item}.",
            )
        else:
            segments[-1]["flight_rule"] = item[0]
    else:
        err["syntax_error"].append(
            f"{item} (after {previous['item']}) must be a Route or DCT or Change of flight rule (IFR/VFR).",
        )
        return None

    return previous


def _parse_route(  # noqa:C901
    data: dict[str, str],
    res: dict[str, str | list[dict[str, str]]],
    err: dict[str, list[str]],
) -> None:
    """Check for syntax errors in the route part of an FPL message.

    Args:
    ----
        data (dict): The FPL data.
        res (dict): Dictionary to store results.
        err (dict): Dictionary to store error messages.

    Returns:
    -------
        None

    """
    # Extract initial speed and level from the route data
    route_items = data["route"].split()
    init_sp_lvl = re.match(patterns.SPEED_LEVEL, route_items[0])
    if init_sp_lvl is not None:
        res["initial_speed"] = init_sp_lvl.groupdict().get("speed")
        res["initial_level"] = init_sp_lvl.groupdict().get("level")
    else:
        err["syntax_error"].append(f"`{route_items[0]}` must be a valid speed & level.")
        return

    # keep a look at item already checked to be able to expect the nature of next item to be checked
    previous: dict[str, str] = {"type": "", "item": ""}

    # route_items[1] must be DCT, Route or Point
    if route_items[1] == "DCT":
        previous = {"type": "dct", "item": "DCT"}

    elif item := re.match(patterns.ROUTE, route_items[1]):
        previous = {"type": "route", "item": item.groupdict().get("route")}

    elif item := re.match(patterns.SID_STAR, route_items[1]):
        previous = {"type": "sid", "item": item.groupdict().get("sid_star")}
        res["sid"] = item.groupdict().get("sid_star")

    elif item := re.match(patterns.POINT, route_items[1]):
        previous = {"type": "point", "item": item.groupdict().get("point")}

    elif item := re.match(patterns.LOCATION, route_items[1]):
        previous = {"type": "location", "item": item.groupdict().get("location")}

    else:
        err["syntax_error"].append(f"`{route_items[1]}` must be a valid ATS Route or DCT or an ATS Point")
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
        },
    ]

    rest_of_route_items = route_items[2:]
    set_rest_of_route_items = set(rest_of_route_items)

    # Check if flight rule needs to be changed and handle error cases
    needs_change_of_flt_rule = res["flight_rule"] in ("Z", "Y")
    if needs_change_of_flt_rule:
        if res["flight_rule"] == "Z" and "IFR" not in set_rest_of_route_items:
            err["syntax_error"].append(
                f"Flight rule is filled as `{res['flight_rule']}` but doesn't change (to IFR) in the route.",
            )
        if res["flight_rule"] == "Y" and "VFR" not in set_rest_of_route_items:
            err["syntax_error"].append(
                f"Flight rule is filled as `{res['flight_rule']}` but doesn't change (to VFR) in the route.",
            )

    # Process each item in the route
    # previous['type'] is one of route,dct,point,location
    for item in rest_of_route_items:
        # NOTE: _update_segments must only be called if item is a SIG_POINT not for DCT or ROUTE or IFR/VFR or etc.
        if previous["type"] in ("route", "sid"):
            # current item can be a point that has an assigned indicator (point, change speed-level, cruise-climb)
            previous = _check_item_is_valid_point_with_indicator(item, previous, segments, err)
            if previous is None:
                return
            _update_segments(segments, previous["item"])
        elif previous["type"] == "dct":
            # current item can be a sig-point
            previous = _check_item_is_valid_point_or_location(item, previous, segments, err)
            if previous is None:
                return
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
            elif matched := re.match(patterns.LOCATION, item):
                previous = {"type": "location", "item": matched.groupdict().get("location")}
                if previous is None:
                    return
                _update_segments(segments, previous["item"])
            else:
                err["syntax_error"].append(
                    f"{item} (after {previous['item']}) must be a valid Sig. Point or the word DCT.",
                )

    # Set the 'to' value for the last segment to the destination aerodrome
    segments[-1]["to"] = res["destination_ad"]

    # Store the route segments in the result dictionary
    res["route"] = segments


def _validate_simple_fields(row_data: dict, parsed_data: dict, err: dict) -> None:
    # Validate callsign
    aircraft_identification = re.match(patterns.AIRCRAFT_IDENTIFICATION, row_data["aircraft_identification"])
    if not aircraft_identification:
        err["syntax_error"].append(
            f"Invalid aircraft identification `{row_data['aircraft_identification']}`.",
        )
    else:
        parsed_data["aircraft_identification"] = aircraft_identification.group()

    # Validate flight rule/type
    flt_rule_type = re.match(patterns.FLIGHT_RULE_AND_TYPE, row_data["flt_rule_type"])
    if not flt_rule_type:
        err["syntax_error"].append(f"Invalid flight rule or type `{row_data['flt_rule_type']}`.")
    else:
        parsed_data.update(flt_rule_type.groupdict())

    # Validate numbers/type/weak
    numbers_type_weak = re.match(patterns.AC_NUMBER_TYPE_WAKE, row_data["numbers_type_weak"])
    if not numbers_type_weak:
        err["syntax_error"].append(
            f"Invalid aircraft number(s), type or weakturbulence category `{row_data['numbers_type_weak']}`.",
        )
    else:
        parsed_data.update(numbers_type_weak.groupdict())

    # Validate equipments/capabilities
    equipments_capabilities = re.match(
        patterns.EQUIPMENTS_CAPABILITIES,
        row_data["equipments_and_capabilities"],
    )
    if not equipments_capabilities:
        err["syntax_error"].append(
            f"Invalid equipments or capabilities `{row_data['equipments_and_capabilities']}`.",
        )
    else:
        parsed_data.update(equipments_capabilities.groupdict())

    # Validate departure aerodrome and time
    dep_ad_time = re.match(patterns.DEPARTURE_AD_TIME, row_data["dep_ad_time"])
    if not dep_ad_time:
        err["syntax_error"].append(f"Invalid departure aerodrome or time `{row_data['dep_ad_time']}`.")
    else:
        parsed_data.update(dep_ad_time.groupdict())

    # Validate destination aerodrome, teet, and alternates
    dest_teet_alt = re.match(patterns.DEST_AD_TEET_ALTS, row_data["dest_teet_alts"])
    if not dest_teet_alt:
        err["syntax_error"].append(
            f"Invalid destination aerodrome or time or alternates `{row_data['dest_teet_alts']}`.",
        )
    else:
        parsed_data.update(dest_teet_alt.groupdict())


def _validate_fpl_item18_other_information(row_data: dict, parsed_data: dict, err: dict) -> None:
    mut_value = row_data["others"][:]
    for key, pattern in patterns.OTHER_INFO_SWITCHES_MAPPING.items():
        cleaned_pattern = pattern.replace(r"^", r"\b").replace(r"$", r"\b")
        matches = list(re.finditer(cleaned_pattern, mut_value))
        if not matches:
            continue
        if len(matches) > 1:
            err["syntax_error"].append(f"Switch `{key}` already exists (ITEM18).")
            continue

        switch_and_value = matches[0].groupdict()
        parsed_data.update(switch_and_value)
        mut_value = mut_value.replace("/".join(*switch_and_value.items()), "")

    if mut_value.strip():
        err["syntax_error"].append(
            f"`{mut_value}` is ambiguous and cannot be recognized as valid other information (ITEM18).",
        )


def parse(
    row_data: dict[str, str],
) -> tuple[dict[str, str | list[dict[str, str]]], dict[str, str] | None]:
    """Check for syntax errors and prepare a new dictionary.

    This function checks for syntax errors in the input and prepares a new dictionary based on the validated data.
    It performs the following tasks:
    - Validates the syntax of the input data.
    - Constructs a new dictionary based on the validated data.

    Args:
    ----
        row_data (dict): The flight plan AFTN message text splitted by dashes.

    Returns:
    -------
    tuple: Tuple of two dictionaries containing the validated data and encountered errors, if any.

    """
    parsed_data = {}
    err = {"syntax_error": []}

    # Parse fields that are simple to parse
    _validate_simple_fields(row_data, parsed_data, err)

    # Parse Other Information
    _validate_fpl_item18_other_information(row_data, parsed_data, err)

    parsed_data = {key.lower(): value for key, value in parsed_data.items()}

    if parsed_data["departure_ad"] in ("ZZZZ", "AFIL"):
        if "dep" not in parsed_data:
            err["syntax_error"].append(
                "DEP is not defined and missing DEP/ switch in ITEM18 (Other information).",
            )
        elif not re.match(patterns.LOCATION, parsed_data["dep"]):
            err["syntax_error"].append(
                f"DEP/ in ITEM18`{parsed_data['dep']}` is not a valid Point, "
                "Coordinate or BearingDistance.",
            )
    elif "dep" in parsed_data:
        err["syntax_error"].append(
            "There must be only one of departure Ad. or DEP/ switch in ITEM18 (Other information).",
        )

    if parsed_data["destination_ad"] == "ZZZZ":
        if "dest" not in parsed_data:
            err["syntax_error"].append(
                "DEST is not defined and missing DEST/ switch in ITEM18 (Other information).",
            )
        elif not re.match(patterns.LOCATION, parsed_data["dest"]):
            err["syntax_error"].append(
                f"DEST/ in ITEM18 `{parsed_data['dest']}` is not a valid Point, "
                "Coordinate or BearingDistance.",
            )
    elif "dest" in parsed_data:
        err["syntax_error"].append(
            "There must be only one of destination Ad. or DEST/ switch in ITEM18 (Other information).",
        )

    if parsed_data["alt_ad_1"] == "ZZZZ" or parsed_data["alt_ad_2"] == "ZZZZ":
        if "altn" not in parsed_data:
            err["syntax_error"].append(
                "ALTN is not defined and missing ALTN/ switch in ITEM18 (Other information).",
            )
        elif not re.match(patterns.LOCATION, parsed_data["dest"]):
            err["syntax_error"].append(
                f"ALTN/ in ITEM18 `{parsed_data['dest']}` is not a valid point or coordinate "
                "(7 or 11 characters) or bearing-distance.",
            )

    if "dof" in parsed_data:
        try:
            dt.datetime.strptime(parsed_data["dof"], "%y%m%d")
        except ValueError:
            err["syntax_error"].append(f"DOF `{parsed_data["dof"]}` is not valid (YYMMDD).")

    # Ensure default date of flight is set to today if not provided
    parsed_data["dof"] = parsed_data.get("dof", dt.datetime.now().date().strftime("%y%m%d"))
    # Calculate departure datetime
    eobt = dt.datetime.strptime(parsed_data["dof"] + parsed_data["eobt"], "%y%m%d%H%M")
    submit_time = dt.datetime.now()
    if not (dt.timedelta(minutes=60) < eobt - submit_time < dt.timedelta(hours=120)):
        err["syntax_error"].append(
            "Flight plans shall not be submitted sooner than 120 hours "
            "nor later than 60 minutes before the estimated off-block time (EOBT).",
        )

    # Parse Route
    _parse_route(row_data, parsed_data, err)

    # TODO: check the insertion of "W" or any alternative in item10(equipments/capabilities) for RVSM/NonRVSM

    errors = {f"{inx}": err for inx, err in enumerate(err["syntax_error"])} if err["syntax_error"] else {}
    return parsed_data, errors
