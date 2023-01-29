import pandas as pd
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from apps.aerodromes.models import Aerodrome
from apps.general.models import FIR
from apps.general.models.abstracts import BasePoint
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
        # parser.add_argument(
        #     "-a", "--aerodromes", action="store_true", help="Create/Update Aerodromes"
        # )
        # parser.add_argument(
        #     "-a", "--aerodromes", action="store_true", help="Create/Update Aerodromes"
        # )
        # parser.add_argument(
        #     "-a", "--aerodromes", action="store_true", help="Create/Update Aerodromes"
        # )
        # parser.add_argument(
        #     "-a", "--aerodromes", action="store_true", help="Create/Update Aerodromes"
        # )

    def handle(self, *args, **kwargs):
        # aerodromes = kwargs["aerodromes"]
        # iatacodes = kwargs["aerodromes_iata_code"]

        # if aerodromes:
        self.create_airports()
        # if iatacodes:
        self.set_ad_iatacode()

    def _get_geo_coordinates(self, coordinates: str):
        latitude, longitude = dms2dd(coordinates)
        location = GEOSGeometry(
            f"POINT({longitude} {latitude})",
            srid=4326,
        )
        return latitude, longitude, location

    def create_airports(self):
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
            adtype = row["TYPE"]
            name = row["NAME OF AIRPORT"]
            ifrvfr = row["IFR/VFR"]
            adtype = adtype.strip().lower()
            name = name.strip().capitalize()
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
            self.stdout.write(self.style.SUCCESS("Aeroromes have been created!"))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def set_ad_iatacode(self):
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
                self.style.SUCCESS("Aeroromes iatacode have been updated!")
            )
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))
