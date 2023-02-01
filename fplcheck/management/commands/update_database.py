import pandas as pd
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from apps.aerodromes.models import Aerodrome
from apps.general.models import FIR
from apps.points.models import NavAid, Point
from apps.routes.models import Route, RouteSection, SidStar
from apps.utils.helpers import dms2dd

IATA = "./resources/YATA CODE.xlsx"
POINTS_FIRS = "./resources/Points.xlsx"
AERODROMES = "./resources/AIRPORTS.xlsx"
NAVAIDS = "./resources/NAVID.xlsx"
SIDSTAR = "./resources/SID & STAR.xlsx"
ROUTES = "./resources/Routes.xlsx"


class Command(BaseCommand):
    help = (
        "Updates Database by first cleaning it and then loading data from excel files "
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--aerodromes", action="store_true", help="Create Aerodromes"
        )
        parser.add_argument(
            "--aerodromes-iata-code",
            action="store_true",
            help="Update Aerodromes IATA Code",
        )
        parser.add_argument("-f", "--firs", action="store_true", help="Create FIRs")
        parser.add_argument("-p", "--points", action="store_true", help="Create Points")
        parser.add_argument(
            "-n", "--navaids", action="store_true", help="Create/Update NAVAIDs"
        )
        parser.add_argument(
            "-s", "--sidstars", action="store_true", help="Create/Update SID-STARS"
        )

    def handle(self, *args, **kwargs):
        aerodromes = kwargs["aerodromes"]
        iatacodes = kwargs["aerodromes_iata_code"]
        firs = kwargs["firs"]
        points = kwargs["points"]
        navaids = kwargs["navaids"]
        sidstars = kwargs["sidstars"]

        # if aerodromes:
        # self.create_airports()
        # # if iatacodes:
        # self.set_ad_iatacode()
        # # if firs:
        # self.create_firs()
        # if navaids:
        self.create_navaids()
        # if points:
        self.create_points()
        # # if sidstars:
        # self.create_sid_stars()

    def _get_geo_coordinates(self, coordinates: str):
        latitude, longitude = dms2dd(coordinates)
        location = GEOSGeometry(
            f"POINT({longitude} {latitude})",
            srid=4326,
        )
        return latitude, longitude, location

    def create_airports(self):
        """Cleans and Creates Aerodromes form excel file"""

        Aerodrome.objects.all().delete()

        df = pd.read_excel(
            AERODROMES,
            usecols=[
                "AIRPORT ICAO LETER",
                "COORDINATES",
                "TYPE",
                "NAME OF AIRPORT",
                "IFR/VFR",
            ],
        )
        lst = []
        for _, row in df.iterrows():
            fl = row["AIRPORT ICAO LETER"]
            cord = row["COORDINATES"]
            adtype = row["TYPE"].strip().lower()
            name = row["NAME OF AIRPORT"].strip().capitalize()
            ifrvfr = row["IFR/VFR"]

            for tp in ("IFR", "VFR", "IFR/VFR"):
                if ifrvfr == tp:
                    ifrvfr = tp.replace("/", "_").lower()
                    break
            else:
                ifrvfr = "VFR"
            lst.append((fl, name, adtype, cord, ifrvfr))

        aerodromes = set()
        for inx, item in enumerate(lst, start=1):
            ad = Aerodrome(
                id=inx,
                four_letters=item[0],
                name=item[1],
                type=item[2],
                coordinates=item[3],
                ifr_vfr=item[4],
            )
            ad.latitude, ad.longitude, ad.location = self._get_geo_coordinates(
                ad.coordinates
            )
            aerodromes.add(ad)
        try:
            Aerodrome.objects.bulk_create(aerodromes)
            self.stdout.write(self.style.SUCCESS("Aeroromes have been created."))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def set_ad_iatacode(self):
        """Sets Aerodromes IATA code from excel file"""

        df = pd.read_excel(IATA)
        data = [
            {"four_letters": row["Airport ICAO ID"], "iatacode": row["Airport IATA ID"]}
            for _, row in df.iterrows()
        ]
        data.sort(key=lambda item: item["four_letters"])
        aerodromes = [item["four_letters"] for item in data]
        updated_ads = []
        ads = Aerodrome.objects.filter(four_letters__in=aerodromes).order_by(
            "four_letters"
        )
        for aerodrome, info in zip(ads, data):
            aerodrome.iatacode = info["iatacode"]
            updated_ads.append(aerodrome)

        try:
            Aerodrome.objects.bulk_update(updated_ads, ["iatacode"])
            self.stdout.write(
                self.style.SUCCESS("Aeroromes iatacode have been updated.")
            )
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def create_firs(self):
        """Cleans and Creates FIRs form excel file"""

        FIR.objects.all().delete()

        df = pd.read_excel(POINTS_FIRS)

        firs = set()
        fir_names = set(
            row["COUNTRY"]
            for _, row in df.iterrows()
            if isinstance(row["COUNTRY"], str) and row["COUNTRY"]
        )
        fir_names.add(settings.FIR_FOUR_LETTERS)
        for inx, four_letters in enumerate(fir_names, start=1):
            firs.add(FIR(id=inx, four_letters=four_letters))

        try:
            FIR.objects.bulk_create(firs)
            self.stdout.write(self.style.SUCCESS("FIRs have been created."))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def create_points(self):
        """Cleans and Creates Points form excel file"""

        Point.objects.all().delete()

        df = pd.read_excel(POINTS_FIRS)

        points_and_firs = []
        for _, row in df.iterrows():
            p_name = row["NAME"]
            p_cors = f'{row["COORDINATES"]}' * isinstance(row["COORDINATES"], str)
            is_fir_bnd = row["FIR BOUNDARY/INSIDE FIR"] == "FIR BOUNDARY"

            point = Point(name=p_name, coordinates=p_cors, is_fir_boundary=is_fir_bnd)

            p_firs = []
            if row["FIR BOUNDARY/INSIDE FIR"] == "INSIDE FIR ":
                p_firs = [settings.FIR_FOUR_LETTERS]
            elif row["FIR BOUNDARY/INSIDE FIR"] == "FIR BOUNDARY":
                p_firs = [settings.FIR_FOUR_LETTERS] + [row["COUNTRY"]]
            points_and_firs.append((point, *p_firs))

            if settings.FIR_FOUR_LETTERS in p_firs and not point.coordinates:
                raise SystemExit(
                    f"Point with name '{point.name}' must have coordinates!"
                )

        points = set()
        for inx, item in enumerate(points_and_firs, start=1):
            point = item[0]
            point.id = inx
            if any(point.name == added_point.name for added_point in points):
                raise SystemExit(f"Point with name '{point.name}' already exists!")
            points.add(point)
        try:
            created_points = Point.objects.bulk_create(points)
            self.stdout.write(self.style.SUCCESS("Points have been created."))

            try:
                for point in created_points:
                    for item in points_and_firs:
                        if point.name == item[0].name:
                            point.fir.add(
                                *FIR.objects.filter(four_letters__in=item[1:])
                            )
                            break
                self.stdout.write(self.style.SUCCESS("Points FIR have been updated."))
            except Exception as err:
                self.stdout.write(self.style.ERROR(err))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def create_navaids(self):
        """Note: just use to store NAVAIDs of settings.FIR_FOUR_LETTERS"""
        NavAid.objects.all().delete()

        current_fir = FIR.objects.get(four_letters=settings.FIR_FOUR_LETTERS)

        df = pd.read_excel(NAVAIDS)
        for _, row in df.iterrows():
            name = row["STATION"]
            name_pl = row["NAME OF AIRPORT"]
            coordinates = f'{row["COORDINATE"]}' * isinstance(row["COORDINATE"], str)
            tp = row["TYPE"].replace("/", "_").lower()
            ad = row["AIRPORT ICAO LETTER"]
            uc = (
                row["USE IN ROUTE/USE IN AIRPORT"]
                .replace("USE ", "")
                .strip()
                .replace(" ", "_")
                .lower()
            )

            if not NavAid.objects.filter(name=name, use_case=uc, type=tp).exists():
                new_nav = NavAid.objects.create(
                    name=name,
                    name_pl=name_pl,
                    type=tp,
                    use_case=uc,
                    coordinates=coordinates,
                )

                new_nav.aerodromes.add(*Aerodrome.objects.filter(four_letters=ad))
                new_nav.fir.add(current_fir)

            else:
                print(row)
        self.stdout.write(self.style.SUCCESS("NavAids have been created."))

    def create_sid_stars(self):

        SidStar.objects.all().delete()

        df = pd.read_excel(SIDSTAR)
        for inx, row in df.iterrows():
            adname = row["AIRPORT"]
            ntp = row["NAVID"].replace("/", "_").lower()
            nvname = row["NAVID NAME"]
            ssname = row["NAME"]
            tp = row["SID/STAR "].upper().replace("/", "_")
            rwy = f'{row["RWY"]}' * isinstance(row["RWY"], str)
            rnp = row["NAVID"] == "RNP"

            ad = Aerodrome.objects.filter(four_letters=adname).first()
            navaid = NavAid.objects.filter(
                name=nvname, type__in=[ntp, *ntp.split("_")]
            ).first()

            spname = ssname[:-2]
            for plname, name in (
                ("SAVEH", "SAV"),
                ("LAVAN", "LVA"),
                ("DEHNAMK", "DHN"),
            ):
                if spname == plname:
                    spname = name
            point = Point.objects.filter(name=spname).first()

            if not SidStar.objects.filter(
                name=ssname, aerodrome=ad, nav_aid=navaid
            ).exists():
                try:
                    SidStar.objects.create(
                        name=ssname,
                        name_pl=ssname,
                        aerodrome=ad,
                        nav_aid=navaid,
                        rnp_app=rnp,
                        point=point,
                        type=tp,
                        rwy=rwy,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"SID-STAR {sidstar} have been created.")
                    )
                except Exception as err:
                    self.stdout.write(self.style.ERROR(err))
                    with open(
                        "./not-created-sid-stars.txt", "a+", encoding="utf-8"
                    ) as dpf:
                        dpf.write(ssname + "\n")
            else:
                sidstar = SidStar.objects.get(name=ssname, aerodrome=ad)
                if sidstar.type != tp:
                    sidstar.type = "SID_STAR"
                    sidstar.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"SID-STAR {sidstar} have been updated.")
                    )
                else:
                    self.stdout.write(self.style.ERROR(str(row)))
                    with open(
                        "./duplicate-sid-stars.txt", "a+", encoding="utf-8"
                    ) as dpf:
                        dpf.write(str(row) + "\n")
                        self.stdout.write(
                            self.style.ERROR(
                                f"SID-STAR {sidstar} considred duplicated."
                            )
                        )
