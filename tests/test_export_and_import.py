import datetime as dt
import random
import string
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.aerodromes.models.aerodrome import Aerodrome
from apps.aerodromes.models.curfew import Curfew
from apps.aerodromes.models.daily_opr import DailyOperationalHour
from apps.aerodromes.models.temp_closure import TemporaryClosure
from apps.general.models.base import FIR
from apps.points.models.navaid import NavAid
from apps.points.models.point import Point
from apps.routes.models.base import Route
from apps.routes.models.sid_star import SidStar
from core.utils.choices import NavAidType, NavAidUseCase, SidStarType
from core.utils.helpers import zipfile_extactor, zipfile_saver
from core.views import export_models


class TestExportAndImport(TestCase):
    def setUp(self):
        fir_indicators = ("OIIX", "OKKK", "UBBB", "OBBB", "OMAE")
        firs = (FIR(indicator=indicator) for indicator in fir_indicators)
        firs = FIR.objects.bulk_create(firs)

        aerodrome_indicators = ("OIII", "OIIE", "OIFM", "OISS", "OIMM")
        aerodrome_coordinates = ("4021N05611E", "4022N05612E", "4023N05613E", "4024N05614E", "4025N05615E")

        aerodromes = (
            Aerodrome(
                indicator=aerodrome_indicator,
                coordinate=aerodrome_coordinate,
            )
            for aerodrome_indicator, aerodrome_coordinate in zip(aerodrome_indicators, aerodrome_coordinates)
        )
        aerodromes = Aerodrome.objects.bulk_create(aerodromes)
        for ad in aerodromes:
            ad.fir.add(FIR.objects.get(indicator="OIIX"))
            ad.save()

        oiii = Aerodrome.objects.get(indicator="OIII")

        today = dt.datetime.today()
        tonight = dt.datetime.combine(today, dt.time(hour=23, minute=30))
        midnight = dt.datetime.combine(today, dt.time(hour=00, minute=00))
        midnight1 = dt.datetime.combine(today, dt.time(hour=23, minute=59))
        tomorrow = today + dt.timedelta(days=1)
        tomorrow_morning = dt.datetime.combine(tomorrow, dt.time(hour=3, minute=30))
        vfr_start_time = dt.datetime.combine(today, dt.time(hour=8, minute=30))
        vfr_end_time = dt.datetime.combine(today, dt.time(hour=17, minute=30))
        tmp_start = dt.datetime.combine(today, dt.time(hour=12, minute=30))
        tmp_end = dt.datetime.combine(today, dt.time(hour=14, minute=30))

        DailyOperationalHour.objects.create(
            aerodrome=oiii,
            date=today,
            start_time=midnight,
            end_time=midnight1,
            vfr_start_time=vfr_start_time,
            vfr_end_time=vfr_end_time,
        )

        Curfew.objects.create(aerodrome=oiii, start=tonight, end=tomorrow_morning)

        TemporaryClosure.objects.create(
            aerodrome=oiii,
            start=tmp_start,
            end=tmp_end,
        )

        navaid_indicators = ("SAV", "DHN", "VR", "RUS", "KRZ")
        navaid_coordinates = ("4031N05641E", "4032N05642E", "4033N05643E", "4034N05644E", "4035N05645E")
        navaids = [
            NavAid.objects.create(
                indicator=indicator,
                coordinate=coordinate,
                type=random.choice(NavAidType.choices)[0],
                usecase=random.choice(NavAidUseCase.choices)[0],
            )
            for indicator, coordinate in zip(navaid_indicators, navaid_coordinates)
        ]

        point_indicators = ("MIVAK", "BOXAM", "DASIS", "NANPI", "ASVIB")
        point_coordinates = ("4041N05651E", "4042N05652E", "4043N05653E", "4044N05654E", "4045N05655E")
        points = [
            Point(indicator=indicator, coordinate=coordinate)
            for indicator, coordinate in zip(point_indicators, point_coordinates)
        ]
        points = Point.objects.bulk_create(points)

        for point in Point.objects.all():
            point.fir.add(FIR.objects.get(indicator="OIIX"))
            point.save()

        sidstars = [
            SidStar(
                aerodrome=aerodrome,
                navaid=navaid,
                point=point,
                type=random.choice(SidStarType.choices)[0],
                indicator=(
                    point.indicator + random.choice(string.digits) + random.choice(string.ascii_uppercase)
                ),
            )
            for aerodrome, navaid, point in zip(aerodromes, navaids, points)
        ]
        SidStar.objects.bulk_create(sidstars)

        Route.objects.bulk_create([Route(indicator="W32"), Route(indicator="A452"), Route(indicator="B411")])

        self.request_factory = RequestFactory()

        # Create a staff user
        User = get_user_model()
        self.user = User.objects.create_user(username="staff_user", password="password", is_staff=True)

        return super().setUp()

    def call_command(self, command, *args, **kwargs):
        out = StringIO()
        call_command(command, *args, stdout=out, stderr=StringIO(), **kwargs)
        return out.getvalue()

    def test_exporting_all_models(self):
        # Create an instance of a GET request.
        request = self.request_factory.get(reverse("export_models"))

        # Simulate a logged-in user by setting request.user manually.
        request.user = self.user

        response = export_models(request)
        self.assertEqual(response.status_code, 200)

        # Specify the directory where you want to save the zip file
        output_dir = "./tests/"

        # Specify the filename for the saved zip file
        zip_filename = "exports.zip"

        self.assertTrue(zipfile_saver(response.content, output_dir, zip_filename))

    def test_import_all_models(self):
        # Specify the path to the downloaded zip file
        zip_file_path = "./tests/exports.zip"

        # Specify the directory where you want to extract the contents
        extract_dir = "./tests/exports/"

        extract_dir = Path(zipfile_extactor(zip_file_path, extract_dir))

        out = self.call_command("update_database", resources=extract_dir)

        self.assertEqual(
            out.splitlines()[-1], BaseCommand().style.SUCCESS("Data has been uploaded successfully.")
        )
