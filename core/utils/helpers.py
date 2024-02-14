"""This module contains Helper functions"""
import re
from decimal import Decimal, getcontext
from itertools import product

import pandas as pd
from django.apps import apps as django_all_apps
from django.core.exceptions import ValidationError
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
    """
    Retrieve all models from the specified app.

    Args:
        app_name (str): The name of the app.

    Returns:
        dict: A dictionary mapping model names to model classes.
    """
    all_models = {
        model.__name__.lower(): model
        for model in django_all_apps.get_models()
        if model._meta.app_config.name.startswith(app_name)
    }
    all_models.pop("route", None)
    return all_models


def get_model_class_and_fields(model_name) -> tuple:
    """
    Retrieve the model class and its fields given a model name.

    Args:
        model_name (str): The name of the model.

    Returns:
        tuple: A tuple containing the model class, its fields, expected fields, and required fields.

    Raises:
        LookupError: If the specified model does not exist.
    """

    # Retrieve all models from the specified app
    model_names_and_classes = get_app_all_models("apps.")

    # Check if the specified model exists
    if model_name not in model_names_and_classes:
        raise LookupError(f"No model with name '{model_name}'.")

    # Get the model class
    model_class = model_names_and_classes.get(model_name)

    # Get all editable and non-auto-created fields of the model
    model_fields = [
        field
        for field in model_class._meta.get_fields(include_parents=True)
        if field.editable and not field.auto_created
    ]

    # Extract verbose names of the fields
    expected_fields = [field.verbose_name.upper() for field in model_fields]

    # Extract verbose names of the required fields
    required_fields = [field.verbose_name.upper() for field in model_fields if field.null is not True]

    return model_class, model_fields, expected_fields, required_fields


def validate_excel_data(df: pd.DataFrame, expected_columns: list[str], required_columns: list[str]):
    """
    Checks if all expected columns are present in the given DataFrame
    and also ensures there are no empty values in any required columns.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to validate.
        expected_columns (list of str): List of expected column names.
        required_columns (list of str): List of required column names.

    Returns:
        none: no return value.

    Raises:
        ValidationError: If expected columns are missing or required columns have empty values.
    """

    # Check for missing expected columns
    missing_cols = sorted(col for col in expected_columns if col not in df.columns)
    if missing_cols:
        raise ValidationError(f"Expected column(s) {missing_cols} are not found.")

    # Check for empty values in required columns
    null_cols = sorted(col for col in required_columns if df[col].isnull().any())
    if null_cols:
        raise ValidationError(f"Required column(s) {null_cols} have empty values.")


def get_model_field_by_uppercased_verbose_name(model_fields, uppercased_verbose_name):
    for mfield in model_fields:
        if mfield.verbose_name.upper() == uppercased_verbose_name:
            return mfield


def field_value_normalize(field, value):
    if isinstance(value, list):
        value = [str(item) for item in value]
        return value

    if isinstance(field, models.CharField) and field.choices:
        for choice_value, choice_label in field.choices:
            if choice_value == value:
                return choice_label

    if isinstance(field, models.ForeignKey):
        if value:
            return str(field.related_model.objects.get(pk=value))
    return value
