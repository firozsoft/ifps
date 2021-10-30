CALLSIGN = r"\b[A-Z\d]{2,7}\b"

FLIGHT_RULE_TYPE = r"\b(?P<flight_rule>[I,V,Y,Z])(?P<flight_type>[S,N,G,M,X]?)\b"

NUMBER_TYPE_WAKE = r"\b(?P<numbers>[\d]{0,2})(?P<type>[A-Z\d]{2,4})\/(?P<weak>[H,M,L,J])\b"

EQUIPMENTS_CAPACITIES = r"\b(?P<equipments>(N|S|A|B|C|D|E1|E2|E3|F|G|H|I|J1|J2|J3|J4|J5|J6|J7|K|L|M1|M2|M3|O|P1|P2|P3|P4|P5|P6|P7|P8|P9|R|T|U|V|W|X|Y|Z)+)\/(?P<capacities>(A|C|E|H|I|L|P|S|X|B1|B2|U1|U2|V1|V2|D1|G1)+)\b"

DEPARTURE_AD_TIME = r"\b((?P<dep_ad>[A-Z]{4})|AFIL|ZZZZ)(?P<eobt>((0|1)[0-9]|2[0-3])[0-5][0-9])\b"

SPEED = r"\b(?P<speed>(K(0|1)[\d]{3})|(N0[\d]{3})|(M(0\d\d|10\d)))\b"
LEVEL = r"\b(?P<level>(F\d\d[0,5])|(S[\d]{3}0)|(A\d\d[0,5])|(M[\d]{4}))\b"

SPEED_LEVEL = r"\b{0}{1}\b".format(SPEED.replace('\\b', ''),
                                   LEVEL.replace('\\b', ''))

POINT = r"\b(?P<point>([A-Z]{2,5})(?<!DCT|IFR|VFR))\b"

SID_STAR = r"\b(?P<sid_star>({0})[\d][A-Z])\b".format(POINT.replace('\\b', ''))

ROUTE = r"\b(?P<route>[A-Z]{1,3}[\d]{1,3})\b"

COR_DEGREES = r"\b(?P<degrees>(([0-8]\d)|90)(N|S)((0\d\d)|(1[0-7]\d)|180)(E|W))\b"

COR_DEG_MINS = r"\b(?P<deg_min>(([0-8]\d)|90)[0-5]\d(N|S)((0\d\d)|(1[0-7]\d)|180)[0-5]\d(E|W))\b"

BEARING_DIST = r"\b(?P<bearing_dist>({0})(([0-2]\d\d)|(3[0-5]\d))[0-2]\d\d)\b".format(
    POINT.replace('\\b', '').replace('<point>', '<ref_point>'))

SIG_POINT = r"\b(?P<sig_point>({0})|({1})|({2})|({3}))\b".format(
    BEARING_DIST.replace('\\b', ''),
    COR_DEGREES.replace('\\b', ''),
    COR_DEG_MINS.replace('\\b', ''),
    POINT.replace('\\b', ''))

CHANGE_SPEED_LEVEL = r"\b(?P<change_speed_level>({0})\/{1})\b".format(
    SIG_POINT.replace('\\b', ''),
    SPEED_LEVEL.replace('\\b', ''))

CHANGE_FLT_RULE = r"\b(?P<change_flt_rule>({0}|({1}))\s(VFR|IFR))\b".format(
    SIG_POINT.replace('\\b', ''), CHANGE_SPEED_LEVEL.replace('\\b', ''))

CRUISECLIMB = r"\b(?P<cruiseclimb>C\/({0})\/({1})(({2})|PLUS))\b".format(
    SIG_POINT.replace('\\b', ''), SPEED_LEVEL.replace('\\b', ''),
    LEVEL.replace('\b', ''))

DESTAD_TEET_ALTS = r"\b(?P<dest_teet_alt>(?P<dest_ad>[A-Z]{4})(?P<teet>[\d]{4})(\s(?P<alt1>[A-Z]{4}))?(\s(?P<alt2>[A-Z]{4}))?)\b"

# Other Info
RNAV_SPC = r"\b(?P<rnav_spc>(A1|B[1-6]|C[1-4]|D[1-4]){1,4})\b"

RNP_SPC = r"\b(?P<rnp_spc>(L1|O[1-4]|S[1-2]|T[1-2]){1,4})\b"

STS = r"\b(?P<sts>STS\/(ALTRV|ATFMX|FFR|FLTCK|HAZMAT|HEAD|HOSP|HUM|MARSA|MEDEVAC|NONRVSM|SAR|STATE))\b"

PBN = r"\b(?P<pbn>PBN\/({0})({1}))\b".format(RNAV_SPC.replace('\b', ''),
                                             RNP_SPC.replace('\b', ''))

NAV = r"\b(?P<nav>NAV\/(?P<nav_key>SBAS|GBAS|ABAS|DGNSS|RTK|WARTK|PPP)(\s(?P=nav_key))?)\b"

COM = r"\b(?P<com>COM\/[A-Z\d]+)\b"

DAT = r"\b(?P<dat>DAT\/[A-Z\d]+)\b"

SUR = r"\b(?P<sur>SUR\/(RSP[\d]{3})(\sRSP[\d]{3})?)\b"

DEP = r"\b(?P<dep>DEP\/(?P<aerodrome>[A-Z]{{4}})|({0})|({1})|({2}))\b".format(
    COR_DEG_MINS.replace('\b', ''),
    BEARING_DIST.replace('\b', ''),
    POINT.replace('\b', ''))

ROUTESCHEME_PATH = r"(\b[A-Z]{2,5}\d[A-Z]\b)?\s(\b[A-Z]{2,5}\b)\s(\b[A-Z]{1,3}[\d]{1,3}\b)\s((\b[A-Z]{2,5}\b)?\s(\b[A-Z]{1,3}[\d]{1,3}\b)?)+\s(\b[A-Z]{2,5}\b)\s(\b[A-Z]{2,5}\d[A-Z]\b)?"

flight_plan_route_pattern = r"speed_level ((route|(DCT point route)) (point at which: change_flt_rule/change_speed_level/change_route)+(route|DCT|(geo_coordinate if both points are geo_coordinates)))|(point|(point at which: change_flt_rule/change_speed_level/change_route) (DCT|(geo_coordinate if both points are geo_coordinates or bearing_and_distance)))"
