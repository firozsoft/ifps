import datetime as dt

import pandas as pd
from django.conf import settings

# from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from apps.aerodromes.models import Aerodrome, DailyOperationalHour
from apps.general.models import FIR
from apps.points.models import NavAid, Point
from apps.routes.models import Route, RouteScheme, RouteSection, SidStar
from core.utils.helpers import dms_to_decimal_degrees

AERODROMES = "./resources/Aerodrome.xlsx"
POINTS_FIRS = "./resources/Point.xlsx"
NAVAIDS = "./resources/NavAid.xlsx"
SIDS_STARS = "./resources/SidStar.xlsx"
ROUTES = "./resources/Route.xlsx"
OPERATIONALHOURS = "./resources/OperationalHour.xlsx"
ROUTE_SCHEMES = "./resources/RouteScheme.xlsx"


class Command(BaseCommand):
    help = (
        "Updates Database by first cleaning it and then loading data from excel files in resources directory"
    )

    def add_arguments(self, parser):
        parser.add_argument("--aerodromes", action="store_true", help="Create Aerodromes")
        parser.add_argument("--firs", action="store_true", help="Create FIRs")
        parser.add_argument("--points", action="store_true", help="Create Points")
        parser.add_argument("--navaids", action="store_true", help="Create/Update Nav.Aids")
        parser.add_argument("--sidstars", action="store_true", help="Create/Update SID-STARS")
        parser.add_argument(
            "--operational-hours",
            action="store_true",
            help="Create/Update Operational Hours",
        )
        parser.add_argument("--routes", action="store_true", help="Create/Update Routes")
        parser.add_argument("--route-schemes", action="store_true", help="Create/Update Route Schemes")

    def handle(self, *args, **kwargs):
        aerodromes = kwargs["aerodromes"]
        firs = kwargs["firs"]
        points = kwargs["points"]
        navaids = kwargs["navaids"]
        sidstars = kwargs["sidstars"]
        operational_hours = kwargs["operational_hours"]
        routes = kwargs["routes"]
        routes = kwargs["route_schemes"]

        # # if firs:
        self.create_firs()
        # if aerodromes:
        # self.create_aerodromes()
        # if navaids:
        # self.create_navaids()
        # if points:
        # self.create_points()
        # # if sidstars:
        # self.create_sid_stars()
        # if operational_hours:
        # self.create_operational_hours()
        # if routes:
        # self.create_routes()
        # if route_schemes:
        # self.create_route_schemes()

    def _get_geo_coordinate(self, coordinate: str):
        latitude, longitude = dms_to_decimal_degrees(coordinate)
        # location = GEOSGeometry(
        #     f"POINT({longitude} {latitude})",
        #     srid=4326,
        # )
        # return latitude, longitude, location
        return latitude, longitude

    def _excel_data_is_valid(
        self,
        df: pd.DataFrame,
        expected_columns_name: list[str],
        required_columns_name: list[str],
    ) -> bool:
        """Checks if all expected_columns are present in the given data frame
        and also there's no empty value in any required_columns

        prints the errors using Commands stdout

        returns boolean (False in case of any error)
        """

        all_expected_cols_found = all(col in df.columns for col in expected_columns_name)

        if not all_expected_cols_found:
            missing_cols = [col for col in expected_columns_name if col not in df.columns]
            self.stdout.write(self.style.ERROR(f"Columns '{missing_cols}' are not found."))
            return False

        for col in required_columns_name:
            if df[col].isnull().any():
                self.stdout.write(self.style.ERROR(f"Column '{col}' has no values."))
                return False

        return True

    def _validate_operational_hours_excel(self, df: pd.DataFrame):
        """Specially for OperationalHours.xlsx it checks if the column sequence is consistent and there is
        no empty/null field in this file

        Returns
            bool
        """

        # Define the required column names
        required_columns = ["DATE", "AD INDICATOR", "IFR START", "IFR END", "SUNRISE", "SUNSET"]

        # Find the index of the 'DATE' column
        date_column_index = df.columns.get_loc("DATE")

        # Check column sequence for each set of columns after 'DATE'
        for i in range(date_column_index + 1, len(df.columns), len(required_columns) - 1):
            columns_to_check = df.iloc[:, i : i + len(required_columns) - 1]
            # Check if columns contain required columns in the specified order
            for j, col in enumerate(columns_to_check.columns):
                if col != required_columns[j + 1]:
                    self.stdout.write(self.style.ERROR(f"Position {j}: Missing column {col}"))
                    return False

        invalid_columns = {}
        for col in df.columns:
            null_rows = df.index[df[col].isnull()].tolist()
            if null_rows:
                invalid_columns[col] = null_rows

        for col, rows in invalid_columns.items():
            self.stdout.write(
                self.style.ERROR(
                    f"Column '{col}' has missing values in rows: {', '.join(str(row) for row in rows)}"
                )
            )

        if invalid_columns:
            return False

        return True

    def create_firs(self):
        """Cleans and Creates FIRs form Excel file"""

        df = pd.read_excel(POINTS_FIRS)

        expected_columns = [
            "FIR",
        ]

        required_columns = expected_columns

        if not self._excel_data_is_valid(df, expected_columns, required_columns):
            return

        FIR.objects.all().delete()

        firs = set()
        fir_names = set(row["FIR"] for _, row in df.iterrows() if isinstance(row["FIR"], str) and row["FIR"])
        fir_names.add(settings.FIR_INDICATOR)
        for inx, indicator in enumerate(fir_names, start=1):
            firs.add(FIR(id=inx, indicator=indicator))

        try:
            FIR.objects.bulk_create(firs)
            self.stdout.write(self.style.SUCCESS("FIRs have been created."))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def create_aerodromes(self):
        """Cleans and Creates Aerodromes form Excel file"""

        df = pd.read_excel(AERODROMES)

        expected_columns = [
            "NAME",
            "INDICATOR",
            "COORDINATE",
            "TYPE",
            "IFR/VFR",
            "IATA Code",
        ]

        required_columns = expected_columns[:-1]

        if not self._excel_data_is_valid(df, expected_columns, required_columns):
            return

        Aerodrome.objects.all().delete()

        lst = []
        for _, row in df.iterrows():
            fl = row["INDICATOR"].strip()
            cord = row["COORDINATE"].strip()
            adtype = row["TYPE"].strip().lower()
            name = row["NAME"].strip().capitalize()
            ifrvfr = row["IFR/VFR"].strip()
            iatacode = row["IATA Code"].strip() if not pd.isnull(row["IATA Code"]) else None

            for tp in ("IFR", "VFR", "IFR/VFR"):
                if ifrvfr == tp:
                    ifrvfr = tp.replace("/", "_").lower()
                    break
            else:
                ifrvfr = "VFR"
            lst.append((fl, name, adtype, cord, ifrvfr, iatacode))

        aerodromes = set()
        for inx, item in enumerate(lst, start=1):
            ad = Aerodrome(
                id=inx,
                indicator=item[0],
                plain_language_name=item[1],
                type=item[2],
                coordinate=item[3],
                ifr_vfr=item[4],
                iatacode=item[5],
            )
            # ad.latitude, ad.longitude, ad.location = self._get_geo_coordinate(
            #     ad.coordinate
            # )
            ad.latitude, ad.longitude = self._get_geo_coordinate(ad.coordinate)
            aerodromes.add(ad)
        try:
            Aerodrome.objects.bulk_create(aerodromes)
            self.stdout.write(self.style.SUCCESS("Aeroromes have been created."))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def create_points(self):
        """Cleans and Creates Points form Excel file"""

        df = pd.read_excel(POINTS_FIRS)

        expected_columns = [
            "NAME",
            "COORDINATE",
            "IS FIR BOUNDARY",
            "FIR",
        ]

        required_columns = expected_columns[:-1]

        if not self._excel_data_is_valid(df, expected_columns, required_columns):
            return

        Point.objects.all().delete()

        points_and_firs = []
        for _, row in df.iterrows():
            p_name = row["NAME"]
            p_cors = f'{row["COORDINATE"]}' * isinstance(row["COORDINATE"], str)
            is_fir_bnd = row["FIR BOUNDARY/INSIDE FIR"] == "FIR BOUNDARY"

            point = Point(name=p_name, coordinate=p_cors, is_fir_boundary=is_fir_bnd)

            p_firs = []
            if row["FIR BOUNDARY/INSIDE FIR"] == "INSIDE FIR ":
                p_firs = [settings.FIR_INDICATOR]
            elif row["FIR BOUNDARY/INSIDE FIR"] == "FIR BOUNDARY":
                p_firs = [settings.FIR_INDICATOR] + [row["COUNTRY"]]
            points_and_firs.append((point, *p_firs))

            if settings.FIR_INDICATOR in p_firs and not point.coordinate:
                raise SystemExit(f"Point with name '{point.name}' must have coordinate!")

        points_and_firs = []
        for point, *firs in points_and_firs:
            try:
                point.full_clean()
                points_and_firs.append((point, *firs))
            except Exception as err:
                self.stdout.write(self.style.ERROR(err))

        created_points = Point.objects.bulk_create(map(lambda tp: tp[0], points_and_firs))
        self.stdout.write(self.style.SUCCESS("Points have been created."))

        point_objects = list(Point.objects.all().order_by("name"))
        created_points.sort(key=lambda point: point.name)

        for tp in zip(point_objects, created_points):
            tp[0].fir.add(*FIR.objects.filter(indicator__in=tp[1][1:]))
        self.stdout.write(self.style.SUCCESS("Points FIR have been updated."))

    def create_navaids(self):
        """Note: just use to store NAVAIDs of settings.FIR_INDICATOR"""
        NavAid.objects.all().delete()

        current_fir = FIR.objects.get(indicator=settings.FIR_INDICATOR)

        df = pd.read_excel(NAVAIDS)
        navids = []
        for _, row in df.iterrows():
            name = row["STATION"]
            name_pl = row["NAME OF AIRPORT"]
            coordinate = f'{row["COORDINATE"]}' * isinstance(row["COORDINATE"], str)
            tp = row["TYPE"].replace("/", "_").lower()
            ad = row["AIRPORT ICAO LETTER"]
            uc = row["USE IN ROUTE/USE IN AIRPORT"].replace("USE ", "").strip().replace(" ", "_").lower()

            navids.append(
                (
                    NavAid(
                        name=name,
                        name_pl=name_pl,
                        type=tp,
                        use_case=uc,
                        coordinate=coordinate,
                    ),
                    Aerodrome.objects.filter(indicator=ad),
                )
            )

        cleaned_navaids = []
        for navaid, ad_qs in navids:
            try:
                navaid.full_clean()
                cleaned_navaids.append(navaid, ad_qs)
            except Exception as err:
                self.stdout.write(self.style.ERROR(err))

        created_navaids = NavAid.objects.bulk_create(map(lambda tp: tp[0], cleaned_navaids))
        self.stdout.write(self.style.SUCCESS("NavAids have been created."))

        navaid_objects = list(NavAid.objects.all().order_by("name"))
        created_navaids.sort(key=lambda tp: tp[0].name)

        for tp in zip(navaid_objects, created_navaids):
            tp[0].aerodromes.add(*tp[1][1])
            tp[0].fir.add(current_fir)
        self.stdout.write(self.style.SUCCESS("NavAids Aerodromes and FIRs have been updated."))

    def create_sid_stars(self):
        SidStar.objects.all().delete()

        df = pd.read_excel(SIDS_STARS)
        for inx, row in df.iterrows():
            adname = row["AIRPORT"]
            ntp = row["NAVID"].replace("/", "_").lower()
            nvname = row["NAVID NAME"]
            ssname = row["NAME"]
            tp = row["SID/STAR "].upper().replace("/", "_")
            rwy = f'{row["RWY"]}' * isinstance(row["RWY"], str)
            rnp = row["NAVID"] == "RNP"

            ad = Aerodrome.objects.filter(indicator=adname).first()
            navaid = NavAid.objects.filter(name=nvname, type__in=[ntp, *ntp.split("_")]).first()

            spname = ssname[:-2]
            for plname, name in (
                ("SAVEH", "SAV"),
                ("LAVAN", "LVA"),
                ("DEHNAMK", "DHN"),
            ):
                if spname == plname:
                    spname = name
            point = Point.objects.filter(name=spname).first()

            if not SidStar.objects.filter(name=ssname, aerodrome=ad, nav_aid=navaid).exists():
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
                    self.stdout.write(self.style.SUCCESS(f"SID-STAR {sidstar} have been created."))
                except Exception as err:
                    self.stdout.write(self.style.ERROR(err))
                    with open("./not-created-sid-stars.txt", "a+", encoding="utf-8") as dpf:
                        dpf.write(ssname + "\n")
            else:
                sidstar = SidStar.objects.get(name=ssname, aerodrome=ad)
                if sidstar.type != tp:
                    sidstar.type = "SID_STAR"
                    sidstar.save()
                    self.stdout.write(self.style.SUCCESS(f"SID-STAR {sidstar} have been updated."))
                else:
                    self.stdout.write(self.style.ERROR(str(row)))
                    with open("./duplicate-sid-stars.txt", "a+", encoding="utf-8") as dpf:
                        dpf.write(str(row) + "\n")
                        self.stdout.write(self.style.ERROR(f"SID-STAR {sidstar} considred duplicated."))

    def create_operational_hours(self):
        """Cleans and Creates OperationalHours form Excel file"""

        df = pd.read_excel(OPERATIONALHOURS)

        if self._validate_operational_hours_excel(df):
            return

        DailyOperationalHour.objects.all().delete()

        for row_inx, row in df.iterrows():
            if (len(row) - 1) % 5 != 0:
                self.stdout.write(self.style.ERROR(f"Error: row: {row_inx}, incorrect number of fields."))
                with open("./not-created-opr-hours.txt", "a+", encoding="utf-8") as dpf:
                    dpf.write(str(row) + "\n")
                continue

            dct = {"date": row["date"]}

            for inx in range(1, len(row), 5):
                dct["aerodrome"] = Aerodrome.objects.filter(indicator=row[inx]).first()
                dct["start_time"] = row[inx + 1]
                dct["end_time"] = row[inx + 2]
                dct["vfr_start_time"] = row[inx + 3]
                dct["vfr_end_time"] = row[inx + 4]

                if dct["start_time"] in ("OR", "HS"):
                    dct["start_time"] = dt.time.min
                if dct["end_time"] in ("OR", "HS"):
                    dct["end_time"] = dt.time.max

                if dct["aerodrome"] is None:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error: row: {row_inx}, col: {inx}-{inx+5}, aerodrome is not deffined"
                        )
                    )
                    print(str(row[inx : inx + 5]))
                    with open("./not-created-opr-hours.txt", "a+", encoding="utf-8") as dpf:
                        dpf.write(str(row) + "\n")
                    continue

                for key in ("start_time", "end_time", "vfr_start_time", "vfr_end_time"):
                    if not isinstance(dct[key], dt.time):
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error: row: {row_inx}, col: {inx}-{inx+5}, an error in a time field"
                            )
                        )
                        print(str(row[inx : inx + 5]))
                        with open("./not-created-opr-hours.txt", "a+", encoding="utf-8") as dpf:
                            dpf.write(str(row) + "\n")
                        break
                else:
                    opr_hours.append(DailyOperationalHour(**dct))

        try:
            DailyOperationalHour.objects.bulk_create(opr_hours)
            self.stdout.write(self.style.SUCCESS("Daily Operational Hours have been created."))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def create_routes(self):
        Route.objects.all().delete()

        has_err = False

        routes = dict()
        df = pd.read_excel(ROUTES)
        for row_inx, row in df.iterrows():
            if row["ROUTE"] not in routes:
                routes[row["ROUTE"]] = [row[1:]]
            else:
                routes[row["ROUTE"]].append(row[1:])

            if row["INSIDE/OUTSIDE FIR"] == "INSIDE":
                # Note: these fields must have values
                # "LOWER", "UPPER", "LATERAL", "DIRECTION", "RNAV5", "MIN RNAV 5", "MAG TR", "DIST"
                if any(pd.isna(cel) for cel in row[4:12]):
                    has_err = True
                    self.stdout.write(self.style.ERROR(f"Error: row: {row_inx}, all fields must have values"))

        if has_err:
            return

        cleaned_routes = list()
        for route in routes:
            rt = Route(name=route)
            try:
                rt.full_clean()
                cleaned_routes.append(rt)
            except Exception as err:
                self.stdout.write(self.style.ERROR(err))

        Route.objects.bulk_create(cleaned_routes)
        self.stdout.write(self.style.SUCCESS("Routes have been created."))

        RQS = Route.objects.all()
        PQS = Point.objects.all()

        cleaned_route_sections = list()
        for route, sections in routes.items():
            rt = RQS.get(name=route)
            for section in sections:
                ps = PQS.filter(name__in=(section["FIRST POINT"], section["SECOND POINT"]))

                rsc = RouteSection(
                    route=rt,
                    point1=ps.get(name=section["FIRST POINT"]),
                    point2=ps.get(name=section["SECOND POINT"]),
                )
                if section["INSIDE/OUTSIDE FIR"] == "INSIDE":
                    rsc.direction = section["DIRECTION"].replace("/", "_").lower()
                    rsc.distance = section["DIST"]
                    rsc.upper_limit = section["UPPER"]
                    rsc.lower_limit = section["LOWER"]
                    rsc.rnav_rnp = section["RNAV5"]
                    rsc.min_rnav_level = section["MIN RNAV 5"]
                    rsc.mag_track = section["MAG TR"]
                    rsc.lateral_limit = section["LATERAL"]
                    rsc.track_coloration = False if section["TRACK CORRELATION"] == "NO" else True
                    rsc.is_active = False if section["ACTIVE"] == "NO" else True
                    rsc.domestic_only = True if section["REMARK"] == "DOMESTIC" else False
                    rsc.not_for_over_flights = True if section["REMARK"] == "Not For OverFlights" else False
                    rsc.remark = section["REMARK"]

                try:
                    rsc.full_clean()
                    cleaned_route_sections.append(rsc)
                except Exception as err:
                    self.stdout.write(self.style.ERROR(err))

        try:
            RouteSection.objects.bulk_create(cleaned_route_sections)
            self.stdout.write(self.style.SUCCESS("Route Sections have been created."))
        except Exception as err:
            self.stdout.write(self.style.ERROR(err))

    def create_route_schemes(self):
        RouteScheme.objects.all().delete()

        df = pd.read_excel(ROUTE_SCHEMES)
        [
            "ENTRY",
            "EXIT",
            "DES",
            "NXT FIR",
            "TYPE RESTRICTION",
            "TRANSITING / LANDING",
            "APPROVED LEVEL",
            "NOT APPROVED LEVEL ",
            "DESCRIPTION",
        ]
        for row_inx, row in df.iterrows():
            print(df.columns)
            break
