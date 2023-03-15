import re

CALLSIGN = r"\b[A-Z[\d]]{2,7}\b"

FLIGHT_RULE_TYPE = r"\b(?P<flight_rule>[I,V,Y,Z])(?P<flight_type>[S,N,G,M,X]?)\b"

NUMBER_TYPE_WAKE = r"\b(?P<numbers>[\d]{0,2})(?P<type>[A-Z[\d]]{2,4})\/(?P<weak>[H,M,L,J])\b"

EQUIPMENTS_CAPACITIES = r"\b(?P<equipments>(N|S|A|B|C|D|E1|E2|E3|F|G|H|I|J[1-7]|K|L|M[1-3]|O|P[1-9]|R|T|U|V|W|X|Y|Z)+)\/(?P<capacities>(A|C|E|H|I|L|P|S|X|B1|B2|U1|U2|V1|V2|D1|G1)+)\b"

DEPARTURE_AD_TIME = r"\b((?P<dep_ad>[A-Z]{4})|AFIL|ZZZZ)(?P<eobt>((0|1)[0-9]|2[0-3])[0-5][0-9])\b"

SPEED = r"\b(?P<speed>(K(0|1)[\d]{3})|(N0[\d]{3})|(M(0[\d][\d]|10[\d])))\b"
LEVEL = r"\b(?P<level>(F[\d][\d][0,5])|(S[\d]{3}0)|(A[\d][\d][0,5])|(M[\d]{4}))\b"

SPEED_LEVEL = r"\b{0}{1}\b".format(SPEED.replace("\\b", ""), LEVEL.replace("\\b", ""))

POINT = r"\b(?P<point>([A-Z]{2,5})(?<!DCT|IFR|VFR))\b"

SID_STAR = r"\b(?P<sid_star>({0})[\d][A-Z])\b".format(POINT.replace("\\b", ""))

ROUTE = r"\b(?P<route>[A-Z]{1,3}[\d]{1,3})\b"

COR_DEGREES = r"\b(?P<degrees>(([0-8][\d])|90)(N|S)((0[\d][\d])|(1[0-7][\d])|180)(E|W))\b"

COR_DEG_MINS = r"\b(?P<deg_min>(([0-8][\d])|90)[0-5][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[0-5][\d](E|W))\b"

COR_DEG_MINS_ACUR = (
    r"\b(?P<deg_min_acur>(([0-8][\d])|90)[\d][\d][\d][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[\d][\d][\d][\d](E|W))\b"
)

BEARING_DIST = r"\b(?P<bearing_dist>({0})(([0-2][\d][\d])|(3[0-5][\d]))[0-2][\d][\d])\b".format(
    POINT.replace("\\b", "").replace("<point>", "<ref_point>")
)

SIG_POINT = r"\b(?P<sig_point>({0})|({1})|({2})|({3}))\b".format(
    BEARING_DIST.replace("\\b", ""),
    COR_DEGREES.replace("\\b", ""),
    COR_DEG_MINS.replace("\\b", ""),
    POINT.replace("\\b", ""),
)

CHANGE_SPEED_LEVEL = r"\b(?P<change_speed_level>({0})\/{1})\b".format(
    SIG_POINT.replace("\\b", ""), SPEED_LEVEL.replace("\\b", "")
)

CHANGE_FLT_RULE = r"\b(?P<change_flt_rule>({0}|({1}))\s(VFR|IFR))\b".format(
    SIG_POINT.replace("\\b", ""), CHANGE_SPEED_LEVEL.replace("\\b", "")
)

CRUISE_CLIMB = r"\b(?P<cruiseclimb>C\/({0})\/({1})(({2})|PLUS))\b".format(
    SIG_POINT.replace("\\b", ""),
    LEVEL.replace("\\b", "").replace("level", "top_level"),
    SPEED_LEVEL.replace("\\b", ""),
)

DEST_AD_TEET_ALTS = (
    r"\b(?P<dest_teet_alt>(?P<dest_ad>[A-Z]{4})(?P<teet>[\d]{4})(\s(?P<alt1>[A-Z]{4}))?(\s(?P<alt2>[A-Z]{4}))?)\b"
)

# Other Info
OTHER_INFO_SWITCHES = [
    "STS",
    "PBN",
    "NAV",
    "COM",
    "DAT",
    "SUR",
    "DOF",
    "REG",
    "EET",
    "SEL",
    "TYP",
    "CODE",
    "DLE",
    "OPR",
    "ORGN",
    "PER",
    "DEP",
    "ALTN",
    "RALT",
    "TALT",
    "RIF",
    "RMK",
]


def _other_switches(switch: str) -> list[str]:
    res = OTHER_INFO_SWITCHES[:]
    res.remove(switch)
    return res


RNAV_SPC = r"\b(?P<RNAV_SPC>(A1|B[1-6]|C[1-4]|D[1-4]){1,4})\b"

RNP_SPC = r"\b(?P<RNP_SPC>(L1|O[1-4]|S[1-2]|T[1-2]){1,4})\b"

STS = (
    r"\bSTS\/(?P<STS>(ALTRV|ATFMX|FFR|FLTCK|HAZMAT|HEAD|HOSP|HUM|MARSA|MEDEVAC|NONRVSM|SAR|STATE)+)"
    + r"(?!("
    + r"|".join(_other_switches("STS"))
    + r"))\b"
)

PBN = (
    r"\bPBN\/(?P<PBN>({0})({1}))".format(RNAV_SPC.replace("\\b", ""), RNP_SPC.replace("\\b", ""))
    + r"(?!("
    + r"|".join(_other_switches("PBN"))
    + r"))\b"
)

NAV = (
    r"\bNAV\/(?P<NAV>(?P<nav_key>SBAS|GBAS|ABAS|DGNSS|RTK|WARTK|PPP)(\s(?P=nav_key))?)"
    + r"(?!("
    + r"|".join(_other_switches("NAV"))
    + r"))\b"
)

COM = r"\bCOM\/(?P<COM>[A-Z[\d]]+)" + r"(?!(" + r"|".join(_other_switches("COM")) + r"))\b"

DAT = r"\bDAT\/(?P<DAT>[A-Z[\d]]+)" + r"(?!(" + r"|".join(_other_switches("DAT")) + r"))\b"

SUR = r"\bSUR\/(?P<SUR>(RSP[\d]{3})(\sRSP[\d]{3})?)" + r"(?!(" + r"|".join(_other_switches("SUR")) + r"))\b"

DOF = (
    r"\bDOF\/(?P<DOF>[\d]{2}((0[\d])|1[0-2])(([0-2][\d])|3[0-1]))"
    + r"(?!("
    + r"|".join(_other_switches("DOF"))
    + r"))\b"
)

REG = r"\bREG\/(?P<REG>[A-Z[\d]]+)" + r"(?!(" + r"|".join(_other_switches("REG")) + r"))\b"

EET = r"\bEET\/(?P<EET>([A-Z]{4}[\d]{4})(\s[A-Z]{4}[\d]{4})*)" + r"(?!(" + r"|".join(_other_switches("EET")) + r"))\b"

SEL = r"\bSEL\/(?P<SEL>[A-Z]+)" + r"(?!(" + r"|".join(_other_switches("SEL")) + r"))\b"

TYP = r"\bTYP\/(?P<TYP>([\d])?[A-Z[\d]]+)" + r"(?!(" + r"|".join(_other_switches("TYP")) + r"))\b"

CODE = r"\bCODE\/(?P<CODE>(F[A-F[\d]]{5})(?<!F00000))" + r"(?!(" + r"|".join(_other_switches("CODE")) + r"))\b"

DLE = (
    r"\bDLE\/(?P<DLE>{0}[\d][\d][0-5][\d])".format(POINT.replace("\\b", ""))
    + r"(?!("
    + r"|".join(_other_switches("DLE"))
    + r"))\b"
)

OPR = r"\bOPR\/(?P<OPR>[A-Z[\d]]+)" + r"(?!(" + r"|".join(_other_switches("OPR")) + r"))\b"

ORGN = r"\bORGN\/(?P<ORGN>[A-Z]{8})" + r"(?!(" + r"|".join(_other_switches("ORGN")) + r"))\b"

PER = r"\bPER\/(?P<PER>[A-Z])" + r"(?!(" + r"|".join(_other_switches("PER")) + r"))\b"

DEP = (
    r"\bDEP\/(?P<DEP>((?P<aerodrome>[A-Z]{{4}})|({0})|({1})|({2}))".format(
        COR_DEG_MINS.replace("\\b", ""),
        BEARING_DIST.replace("\\b", ""),
        POINT.replace("\\b", ""),
    )
    + r"(?!("
    + r"|".join(_other_switches("DEP"))
    + r")))\b"
)

ALTN = DEP.replace(r"DEP\/", r"ALTN\/", 2)

RALT = DEP.replace(r"DEP\/", r"RALT\/", 2)

TALT = DEP.replace(r"DEP\/", r"TALT\/", 2)

ROUTESCHEME_PATH = r"(\b[A-Z]{2,5}[\d][A-Z]\b)?\s(\b[A-Z]{2,5}\b)\s(\b[A-Z]{1,3}[\d]{1,3}\b)\s((\b[A-Z]{2,5}\b)?\s(\b[A-Z]{1,3}[\d]{1,3}\b)?)+\s(\b[A-Z]{2,5}\b)\s(\b[A-Z]{2,5}[\d][A-Z]\b)?"

RIF = (
    r"\b(?P<RIF>{0}\s(?P<revised_dest_ad>[A-Z]{{4}}))\b".format(ROUTESCHEME_PATH.replace("\\b", ""))
    + r"(?!("
    + r"|".join(_other_switches("RIF"))
    + r"))\b"
)

RMK = r"\bRMK\/(?P<RMK>\w+)" + r"(?!(" + r"|".join(_other_switches("RMK")) + r"))\b"

# fmt: off
flight_plan_route_pattern = (
    r"{speed_level} ({SID_STAR}|DCT {point} {route}) "
    r"(({point}|{CHANGE_SPEED_LEVEL}|{CHANGE_FLT_RULE}|{route}) )+"
    r" ({SID_STAR}|{point})$"
).format(
    speed_level=SPEED_LEVEL.replace("\\b", ""),
    SID_STAR=SID_STAR.replace("\\b", ""),
    route=ROUTE.replace("\\b", ""),
    point=SIG_POINT.replace("\\b", ""),
    CHANGE_SPEED_LEVEL=CHANGE_SPEED_LEVEL.replace("\\b", ""),
    CHANGE_FLT_RULE=CHANGE_FLT_RULE.replace("\\b", ""),
)


fpl_route_pattern = re.sub(r"\?P<\w+>", "", flight_plan_route_pattern)
fpl_route_pattern = r"((K(0|1)[\d]{3})|(N0[\d]{3})|(M(0[\d][\d]|10[\d])))((F[\d][\d][0,5])|(S[\d]{3}0)|(A[\d][\d][0,5])|(M[\d]{4})) ((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))[\d][A-Z])|DCT (((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2][\d][\d])|(3[0-5][\d]))[0-2][\d][\d]))|(((([0-8][\d])|90)(N|S)((0[\d][\d])|(1[0-7][\d])|180)(E|W)))|(((([0-8][\d])|90)[0-5][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[0-5][\d](E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))) ([A-Z]{1,3}[\d]{1,3})) (((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2][\d][\d])|(3[0-5][\d]))[0-2][\d][\d]))|(((([0-8][\d])|90)(N|S)((0[\d][\d])|(1[0-7][\d])|180)(E|W)))|(((([0-8][\d])|90)[0-5][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[0-5][\d](E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR))))|(((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2][\d][\d])|(3[0-5][\d]))[0-2][\d][\d]))|(((([0-8][\d])|90)(N|S)((0[\d][\d])|(1[0-7][\d])|180)(E|W)))|(((([0-8][\d])|90)[0-5][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[0-5][\d](E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))))\/((K(0|1)[\d]{3})|(N0[\d]{3})|(M(0[\d][\d]|10[\d])))((F[\d][\d][0,5])|(S[\d]{3}0)|(A[\d][\d][0,5])|(M[\d]{4})))|(((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2][\d][\d])|(3[0-5][\d]))[0-2][\d][\d]))|(((([0-8][\d])|90)(N|S)((0[\d][\d])|(1[0-7][\d])|180)(E|W)))|(((([0-8][\d])|90)[0-5][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[0-5][\d](E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR))))|((((((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2][\d][\d])|(3[0-5][\d]))[0-2][\d][\d]))|(((([0-8][\d])|90)(N|S)((0[\d][\d])|(1[0-7][\d])|180)(E|W)))|(((([0-8][\d])|90)[0-5][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[0-5][\d](E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))))\/((K(0|1)[\d]{3})|(N0[\d]{3})|(M(0[\d][\d]|10[\d])))((F[\d][\d][0,5])|(S[\d]{3}0)|(A[\d][\d][0,5])|(M[\d]{4})))))\s(VFR|IFR))|([A-Z]{1,3}[\d]{1,3})) )+ ((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))[\d][A-Z])|(((((([A-Z]{2,5})(?<!DCT|IFR|VFR)))(([0-2][\d][\d])|(3[0-5][\d]))[0-2][\d][\d]))|(((([0-8][\d])|90)(N|S)((0[\d][\d])|(1[0-7][\d])|180)(E|W)))|(((([0-8][\d])|90)[0-5][\d](N|S)((0[\d][\d])|(1[0-7][\d])|180)[0-5][\d](E|W)))|((([A-Z]{2,5})(?<!DCT|IFR|VFR)))))$"
