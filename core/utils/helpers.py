"""This module contains Helper functions"""
import io
import re
from decimal import Decimal, getcontext
from itertools import product

import pandas as pd
from django.apps import apps as django_all_apps
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import model_to_dict

from core.utils.choices import NavAidType, NavAidUseCase


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


def get_geo_coordinate(coordinate: str):
    latitude, longitude = dms2dd(coordinate)
    # location = GEOSGeometry(
    #     f"POINT({longitude} {latitude})",
    #     srid=4326,
    # )
    # return latitude, longitude, location
    return latitude, longitude


def generate_routes_from_route_scheme_text(string: str) -> list[str]:
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


def field_value_human_readable(field, value):
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


def field_value_codeword(field, human_readable_value) -> str | models.QuerySet:
    if isinstance(field, models.CharField) and field.choices:
        for choice_value, choice_label in field.choices:
            if choice_label == human_readable_value:
                return choice_value

    if isinstance(field, models.ForeignKey):
        dunder_str = map(str.strip, human_readable_value.split("-"))
        if len(dunder_str) == 3:  # Only for NavAid the __str__ returns "indicator - type - use_case"
            name, type_display, use_case_display = dunder_str
            type = [
                choice_value
                for choice_value, choice_label in NavAidType.choices
                if choice_label == type_display
            ].pop()
            use_case = [
                choice_value
                for choice_value, choice_label in NavAidUseCase.choices
                if choice_label == use_case_display
            ].pop()
            return field.related_model.objects.filter(indicator=name, type=type, use_case=use_case)
        return field.related_model.objects.filter(indicator=dunder_str)
    return human_readable_value


def model_to_excel_bytesio(model_name: str) -> io.BytesIO:
    # Get the model class and fields
    model_class, model_fields, expected_fields_for_excel, required_fields = get_model_class_and_fields(
        model_name
    )

    exportable_fields = [model_field.name for model_field in model_fields]

    # Retrieve data from the database
    # excel columns have to be field.verbose_name.upper and they'r values should be human readable
    # but model_to_dict dict is a key value pair of model field.name and field.value
    # the logic below is used to change dict key from field.name to field.verbose_name
    field_name_to_vbname = {
        model_field.name: model_field.verbose_name.upper() for model_field in model_fields
    }
    field_name_to_obj = {model_field.name: model_field for model_field in model_fields}
    data = [
        {
            field_name_to_vbname[field]: field_value_human_readable(field_name_to_obj[field], value)
            for field, value in model_to_dict(instance, fields=exportable_fields).items()
        }
        for instance in model_class.objects.all()
    ]

    # Create a DataFrame from the data
    df = pd.DataFrame(data=data, columns=expected_fields_for_excel)

    # Create a BytesIO object to store the Excel file
    excel_buffer = io.BytesIO()

    # Write the DataFrame to the BytesIO object as an Excel file
    df.to_excel(excel_buffer, index=False)

    return excel_buffer
