"""Points Related Checks Module
    this module contains about:
        ✘🗸 Break each section into smaller sections as possible
        ✘🗸 Check compliance with the restrictions of each section:
           ✘🗸 Routes existence
           ✘🗸 Points existence
           ✘🗸 Routes and Points compatibility
           ✘🗸 Level compliance
           ✘🗸 Routes directions compliance
           ✘🗸 Route Schemes compliance
"""
from typing import Union

from apps.aerodromes.models import Aerodrome
from apps.routes.models import SidStar


def routes_checks(data: dict[str, Union[str, list[dict[str, str]]]], err: dict[str, str]):
    """{"from": "EHAM",
        "to": "LEK",
        "via": "LEK2B",
        "speed": "K0830",
        "level": "F290",
        "top_level": "F290",
        "flight_rule": "I"
        }"""
    for section in data['route']:
        pass

