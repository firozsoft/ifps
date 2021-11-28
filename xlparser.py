import pandas as pd

from apps.aerodromes.models import Aerodrome
from apps.general.models import FIR
from apps.points.models import NavAid, Point


IATA = '../resources/YATA CODE.xlsx'
POINTS_FIRS = '../resources/Points.xlsx'
AERODROMES = '../resources/AIRPORTS.xlsx'
NAVAIDS = '../resources/NAVID.xlsx'
SIDSTAR = '../resources/SID & STAR.xlsx'


def create_firs_and_points() -> None:
    df = pd.read_excel(POINTS_FIRS)
    for row in df.iterrows():
        pname = row[1]["NAME"]
        pcors = row[1]["COORDINATES"]
        is_fir_bnd = True if row[1]["FIR BOUNDARY/INSIDE FIR"] == "FIR BOUNDARY" else False
        if not Point.objects.filter(name=pname).exists():
            newp = Point.objects.create(name=pname, coordinates=pcors, is_fir_boundary=is_fir_bnd)
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
                    elif type(fir_name) != float:
                        fir_id = FIR.objects.create(name=fir_name)
                        newp.fir.add(fir_id)


def create_airports() -> None:
    df = pd.read_excel(AERODROMES)
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
        if not Aerodrome.objects.filter(four_letters=fl).exists():
            Aerodrome.objects.create(four_letters=fl, name=name, type=adtype, coordinates=cord, ifr_vfr=ifrvfr)
        else:
            print(fl)


def set_ad_iata_code() -> None:
    df = pd.read_excel(IATA)
    for row in df.iterrows():
        if ad := Aerodrome.objects.filter(name=row[1]['Airport ICAO ID']).first():
            ad.iatacode = row[1]['Airport IATA ID']
            ad.save()


def create_nav_aid() -> None:
    df = pd.read_excel(NAVAIDS)
    for row in df.iterrows():
        name = row[1]['STATION']
        name_pl = row[1]['NAME OF AIRPORT']
        coordinates = row[1]['COORDINATE'] if type(row[1]['COORDINATE']) != float else None
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
            new_nav = NavAid.objects.create(name=name, name_pl=name_pl, type=tp, use_case=uc, coordinates=coordinates)
            if type(ad) != float and (ard := Aerodrome.objects.filter(four_letters=ad).first()):
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
        rwy = rwy if type(rwy) != float else None
        rnp = True if row[1]["NAVID"] == "RNP" else False
        ad = Aerodrome.objects.filter(four_letters=adname).first()
        navaid = NavAid.objects.filter(name=nvname, type=ntp).first()
        if not navaid:
            navaid = NavAid.objects.filter(name=nvname, type=ntp.split('_')[0]).first()
        print(navaid)
        # point = Point.objects.filter(name=ssname[:-2]).first()
        # if not SidStar.objects.filter(name=ssname).exists():
        #     SidStar.objects.create(name=ssname, name_pl=ssname, \
        #                                      nav_aid=navaid, rnp_app=rnp, \
        #                                      point=point, type=tp, rwy=rwy)
        # else:
        #     import json
        #     with open('./duplicate-sid-stars.txt', 'a+') as dpf:
        #         dpf.write(str(row[1]))
        #


def create_routes_and_route_sections(df: pd.DataFrame) -> None:
    for row in df.iterrows():
        print(row)

