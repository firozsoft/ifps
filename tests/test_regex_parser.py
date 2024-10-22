import datetime as dt

from django.test import TestCase

from core.analyzers import parser


class ParserTestCase(TestCase):
    def data_bakery(self, message):
        parts = list(map(str.strip, message.split("-")))
        return {
            "aircraft_identification": parts[1],
            "flt_rule_type": parts[2],
            "numbers_type_weak": parts[3],
            "equipments_and_capabilities": parts[4],
            "dep_ad_time": parts[5],
            "route": parts[6],
            "dest_teet_alts": parts[7],
            "others": parts[8].replace(")", ""),
        }

    def test_parser_parse(self):
        eobt = (dt.datetime.now() + dt.timedelta(hours=2.5)).time().strftime("%H%M")
        today = dt.datetime.now().date().strftime("%y%m%d")
        fpl_message = (
            f"(FPL-ACF402-IN-EA30/H-S/C-EHAM{eobt}-K0830F290 LEK2B LEK UA6 XMM/M078F330 UA6 "
            "PON DCT URION DCT CHW UA5 NTS DCT 4611N00412W DCT STG UA5 FATIM FATIM1A"
            f"-LPPT0230 LPPR -REG/FBVGA SEL/EJFL DOF/{today} EET/LPPC0158"
            "-E/0345 P/300 R/UVE S/PDJ J/UV D/11 330 C YELLOW A/WHITE C/DENKE)"
        )
        filled_data = self.data_bakery(fpl_message)
        fpl, err = parser.parse(filled_data)
        self.assertEqual(err, {})
        self.assertDictEqual(
            fpl,
            {
                "aircraft_identification": "ACF402",
                "flight_rule": "I",
                "type_of_flight": "N",
                "number_of_aircraft": "",
                "type": "EA30",
                "weakturbulence_category": "H",
                "equipments": "S",
                "capabilities": "C",
                "departure_ad": "EHAM",
                "eobt": f"{eobt}",
                "dest_teet_alt": "LPPT0230 LPPR",
                "destination_ad": "LPPT",
                "teet": "0230",
                "alt_ad_1": "LPPR",
                "alt_ad_2": None,
                "dof": f"{today}",
                "reg": "FBVGA",
                "eet": "LPPC0158",
                "sel": "EJFL",
                "initial_speed": "K0830",
                "initial_level": "F290",
                "sid": "LEK2B",
                "star": "FATIM1A",
                "route": [
                    {
                        "from": "EHAM",
                        "to": "LEK",
                        "via": "LEK2B",
                        "speed": "K0830",
                        "level": "F290",
                        "top_level": "F290",
                        "flight_rule": "I",
                    },
                    {
                        "from": "LEK",
                        "to": "XMM",
                        "via": "UA6",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                    },
                    {
                        "from": "XMM",
                        "to": "PON",
                        "via": "UA6",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                    },
                    {
                        "from": "PON",
                        "to": "URION",
                        "via": "DCT",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                        "nonessential": True,
                    },
                    {
                        "from": "URION",
                        "to": "CHW",
                        "via": "DCT",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                        "nonessential": True,
                    },
                    {
                        "from": "CHW",
                        "to": "NTS",
                        "via": "UA5",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                        "nonessential": True,
                    },
                    {
                        "from": "NTS",
                        "to": "4611N00412W",
                        "via": "DCT",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                        "nonessential": True,
                    },
                    {
                        "from": "4611N00412W",
                        "to": "STG",
                        "via": "DCT",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                        "nonessential": True,
                    },
                    {
                        "from": "STG",
                        "to": "FATIM",
                        "via": "UA5",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                        "nonessential": True,
                    },
                    {
                        "from": "FATIM",
                        "to": "LPPT",
                        "via": "FATIM1A",
                        "speed": "M078",
                        "level": "F330",
                        "top_level": "F330",
                        "flight_rule": "I",
                        "nonessential": True,
                    },
                ],
            },
        )
