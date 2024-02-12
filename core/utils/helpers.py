"""This module contains Helper functions"""
import re
from decimal import Decimal, getcontext
from itertools import product

from django.apps import apps as django_all_apps
from django.db import models


def levels_to_fl_int(row_flight_levels):
    meter = 1
    feet = 3.281 * meter
    if row_flight_levels[0] in ("S", "M"):
        return int(row_flight_levels[1:]) * feet
    return int(row_flight_levels[1:])


def dms2dd(coordinate: str) -> tuple[Decimal, Decimal]:
    """
    Convert degrees or degrees+minutes or degrees+minutes+seconds to decimal-degrees.
    46N078W -> (46 78) or 4620N07805W -> (46.333333 78.083333)
    """
    pattern = r"\b(?P<latitude>(\d{2}|\d{4}|\d{6})(N|S))(?P<longitude>(\d{3}|\d{5}|\d{7})(W|E))\b"
    try:
        lat, long = re.match(pattern, coordinate).groupdict().items()
    except AttributeError as attr_error:
        raise ValueError(f"Invalid coordinate: {coordinate}") from attr_error

    def convertor(lat_or_lang, string):
        getcontext().prec = 8
        neg = string[-1] in "SW"
        string = string[:-1]
        spot = lat_or_lang == "latitude"
        deg, minutes = string[: 3 - spot], string[3 - spot :]
        if len(minutes) > 2:
            minutes, seconds = minutes[:2], minutes[2:]
            return (-1) ** neg * (
                Decimal(deg) + Decimal(minutes) / 60 + (Decimal(seconds) / 3600 if seconds else 0)
            )
        return (-1) ** neg * (Decimal(deg) + (Decimal(minutes) / 60 if minutes else 0))

    return convertor(*lat), convertor(*long)


def generate_route_from_route_scheme_text(string: str) -> list[str]:
    return list(map(" ".join, product(*map(lambda s: s.split("/"), string.split()))))


def get_app_all_models(app_name: str) -> dict[str, models.Model]:
    return {
        model._meta.model_name: model
        for model in django_all_apps.get_models()
        if model._meta.app_config.name.startswith(app_name)
    }


def get_model_class_and_fields(model_name):
    model_names_and_classes = get_app_all_models("apps.")
    if model_name not in model_names_and_classes:
        raise LookupError(f"No model with name '{model_name}'.")

    model_class = model_names_and_classes.get(model_name)

    model_fields = [
        field for field in model_class._meta.get_fields() if field.editable and not field.auto_created
    ]

    expected_fields = [field.verbose_name.upper() for field in model_fields]
    required_fields = [field.verbose_name.upper() for field in model_fields if field.null is not True]

    return model_class, model_fields, expected_fields, required_fields
