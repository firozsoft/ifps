from re import A

import pandas as pd

from apps.aerodromes.models import Aerodrome
from apps.general.models import FIR
from apps.points.models import NavAid, Point
from apps.routes.models import Route, RouteSection, SidStar

IATA = './resources/YATA CODE.xlsx'
POINTS_FIRS = './resources/Points.xlsx'
AERODROMES = './resources/AIRPORTS.xlsx'
NAVAIDS = './resources/NAVID.xlsx'
SIDSTAR = './resources/SID & STAR.xlsx'
ROUTES = './resources/Routes.xlsx'


def create_firs_and_points() -> None:
    df = pd.read_excel(POINTS_FIRS)
    for row in df.iterrows():
        pname = row[1]["NAME"]
        pcors = row[1]["COORDINATES"]
        is_fir_bnd = True if row[1]["FIR BOUNDARY/INSIDE FIR"] == "FIR BOUNDARY" else False
        if not Point.objects.filter(name=pname).exists():
            newp = Point.objects.create(
                name=pname,
                coordinates=pcors,
                is_fir_boundary=is_fir_bnd)
            pfir = None
            if row[1]["FIR BOUNDARY/INSIDE FIR"] == "INSIDE FIR ":
                pfir = ["OIIX"]
            elif row[1]["FIR BOUNDARY/INSIDE FIR"] == "FIR BOUNDARY":
                pfir = ["OIIX"] + [row[1]["COUNTRY"]]
            if pfir:
                for fir_name in pfir:
                    if FIR.objects.filter(name=fir_name).exists():
                        fir_id = FIR.objects.get(name=fir_name)
                        newp.fir.add(fir_id)
                    elif not isinstance(fir_name, float):
                        fir_id = FIR.objects.create(name=fir_name)
                        newp.fir.add(fir_id)


def create_airports() -> None:
    df = pd.read_excel(AERODROMES)
    lst = []
    for row in df.iterrows():
        fl = row[1]["AIRPORT ICAO LETER"]
        cord = row[1]["COORDINATES"]
        adtype = row[1]["TYPE"]
        name = row[1]["NAME OF AIRPORT"]
        ifrvfr = row[1]["IFR/VFR"]
        adtype = adtype.strip().lower()
        name = name.strip().capitalize()
        for tp in ("IFR", "VFR", "IFR/VFR"):
            if ifrvfr == tp:
                ifrvfr = tp.replace('/', '_').lower()
                break
        else:
            ifrvfr = "VFR"
        lst.append(
            (fl, name, adtype, cord, ifrvfr)
        )

    for item in lst:
        if not Aerodrome.objects.filter(four_letters=item[0]).exists():
            Aerodrome.objects.create(four_letters=item[0], name=item[1],
                                     type=item[2], coordinates=item[3],
                                     ifr_vfr=item[4])
        else:
            print(fl)


def set_ad_iata_code() -> None:
    df = pd.read_excel(IATA)
    for row in df.iterrows():
        if ad := Aerodrome.objects.filter(
                name=row[1]['Airport ICAO ID']).first():
            ad.iatacode = row[1]['Airport IATA ID']
            ad.save()


def create_nav_aid() -> None:
    df = pd.read_excel(NAVAIDS)
    for row in df.iterrows():
        name = row[1]['STATION']
        name_pl = row[1]['NAME OF AIRPORT']
        coordinates = row[1]['COORDINATE'] if not isinstance(
            row[1]['COORDINATE'], float) else None
        tp = row[1]['TYPE']
        ad = row[1]['AIRPORT ICAO LETTER']
        uc = row[1]['USE IN ROUTE/USE IN AIRPORT']
        tp = tp.replace('/', '_').lower()
        if uc == "USE IN AIRPORT":
            uc = "in_airport"
        elif uc == "USE IN ROUTE":
            uc = "in_route"
        else:
            uc = "both"
        if not NavAid.objects.filter(name=name, use_case=uc, type=tp).exists():
            new_nav = NavAid.objects.create(
                name=name, name_pl=name_pl, type=tp, use_case=uc,
                coordinates=coordinates)
            if not isinstance(ad, float) and (
                ard := Aerodrome.objects.filter(
                    four_letters=ad).first()):
                ard.nav_aids.add(new_nav)
            new_nav.fir.add(FIR.objects.get(name="OIIX"))
        else:
            print(row)


def create_sid_star() -> None:
    df = pd.read_excel(SIDSTAR)
    for row in df.iterrows():
        adname = row[1]['AIRPORT']
        ntp = row[1]["NAVID"]
        ntp = ntp.replace('/', '_').lower()
        nvname = row[1]['NAVID NAME']
        ssname = row[1]["NAME"]
        tp = row[1]["SID/STAR "]
        tp = tp.upper().replace('/', '_')
        rwy = row[1]["RWY"]
        rwy = rwy if not isinstance(rwy, float) else None
        rnp = True if row[1]["NAVID"] == "RNP" else False
        ad = Aerodrome.objects.filter(four_letters=adname).first()
        navaid = NavAid.objects.filter(name=nvname, type=ntp).first()
        if not navaid:
            navaid = NavAid.objects.filter(
                name=nvname, type=ntp.split('_')[0]).first()
        spname = ssname[:-2]
        for plname in (('SAVEH', "SAV"), ('LAVAN', "LVA"), ("DEHNAMK", "DHN")):
            if spname == plname[0]:
                spname = plname[1]
        point = Point.objects.filter(name=spname).first()
        if not SidStar.objects.filter(
                name=ssname,
                aerodrome=ad,
                nav_aid=navaid).exists():
            try:
                SidStar.objects.create(
                    name=ssname,
                    name_pl=ssname,
                    aerodrome=ad,
                    nav_aid=navaid,
                    rnp_app=rnp,
                    point=point,
                    type=tp,
                    rwy=rwy)
            except Exception:
                with open('./not-created-sid-stars.txt', 'a+') as dpf:
                    dpf.write(ssname)
        else:
            sidstar = SidStar.objects.get(name=ssname, aerodrome=ad)
            if sidstar.type != tp:
                sidstar.type = "SID_STAR"
                sidstar.save()
            else:
                with open('./duplicate-sid-stars.txt', 'a+') as dpf:
                    dpf.write(str(row[1]))


def create_routes_and_route_sections() -> None:
    df = pd.read_excel(ROUTES)
    dct: dict[list] = {}
    for row in df.iterrows():
        rname = row[1]['ROUTE']
        fpoint = row[1]['FIRST POINT'].replace('?', '').replace('!', '')
        spoint = row[1]['SECOND POINT'].replace('?', '').replace('!', '')
        infir = row[1]['INSIDE/OUTSIDE FIR']
        lower_lim = row[1]['LOWER'] if not isinstance(
            row[1]['LOWER'], float) else 1
        upper_lim = row[1]['UPPER'] if not isinstance(
            row[1]['UPPER'], float) else 1
        lat_sep = row[1]['LATERAL'] if not isinstance(
            row[1]['LATERAL'], float) else 1
        dir = row[1]['DIRECTION'] if not isinstance(
            row[1]['DIRECTION'], float) else 1
        rnav = row[1]['RNAV5'] if not isinstance(
            row[1]['RNAV5'], float) else 1
        min_rnav = row[1]['MIN RNAV 5'] if not isinstance(
            row[1]['MIN RNAV 5'], float) else 1
        mag_tr = row[1]['MAG TR'] if not isinstance(
            row[1]['MAG TR'], float) else 1
        dist = row[1]['DIST'] if not isinstance(
            row[1]['DIST'], float) else 1
        active = row[1]['ACTIVE'] if not isinstance(
            row[1]['ACTIVE'], float) else 1
        active = True if active == "YES" else False
        tr_cor = row[1]['TRACK COROLATION'] if not isinstance(
            row[1]['TRACK COROLATION'], float) else 1
        tr_cor = True if tr_cor == "YES" else False
        if rname not in dct.keys():
            dct[rname] = [
                [fpoint, spoint, infir, lower_lim, upper_lim,
                 lat_sep, dir, rnav, min_rnav, mag_tr, dist, active, tr_cor]
            ]
        else:
            dct[rname].append(
                [fpoint, spoint, infir, lower_lim, upper_lim,
                 lat_sep, dir, rnav, min_rnav, mag_tr, dist, active, tr_cor]
            )

    for key, parts in dct.items():
        for part in parts:
            if not (route := Route.objects.filter(name=key).first()):
                route = Route.objects.create(name=key)
            if not (p1 := Point.objects.filter(name=part[0]).first()):
                print('Point 1:', part[0], 'does not exists!')
                continue
            if not (p2 := Point.objects.filter(name=part[1]).first()):
                print('Point 2:', part[1], 'does not exists!')
                continue
            part[0], part[1] = p1, p2
            if not RouteSection.objects.filter(
                    route=route, point1=part[0], point2=part[1]).exists():
                RouteSection.objects.create(route=route,
                                            point1=part[0],
                                            point2=part[1],
                                            lower_limit=part[3],
                                            upper_limit=part[4],
                                            lateral_limit=part[5],
                                            direction=part[6],
                                            rnav_rnp=part[7],
                                            min_rnav_level=part[8],
                                            mag_track=part[9],
                                            distance=part[10],
                                            is_active=part[11],
                                            track_coloration=part[12])
            else:
                print(route, part[0], part[1])
