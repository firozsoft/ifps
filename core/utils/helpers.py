"""Helper functions module"""

import io
from itertools import product
from typing import Union

import pandas as pd
from django.apps import apps as django_all_apps
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import model_to_dict

from core.utils.choices import NavAidType, NavAidUseCase

MODELS_REQUIRING_FILTERING_FOR_EXPORT = [
    "aircraft",
    "fidsdata",
    "flightplan",
    "notam",
    "route",
]


def feet_to_flight_level(altitude_feet: float):
    return round(altitude_feet / 100)


def meters_to_flight_level(altitude_meters: float):
    altitude_feet = altitude_meters * 3.28084
    return feet_to_flight_level(altitude_feet)


def generate_routes_from_route_scheme_text(string: str) -> list[str]:
    """Generate routes from route scheme text"""
    return list(map(" ".join, product(*map(lambda s: s.split("/"), string.split()))))


def get_app_all_exportable_models(app_name: str) -> dict[str, models.Model]:
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
    return all_models


def get_app_all_exportable_models_with_restriction(app_name: str) -> dict[str, models.Model]:
    """
    Retrieve all models from the specified app except those have restrictions to export all instances.

    Args:
        app_name (str): The name of the app.

    Returns:
        dict: A dictionary mapping model names to model classes.
    """
    all_models = {
        key: value
        for key, value in get_app_all_exportable_models(app_name).items()
        if key not in MODELS_REQUIRING_FILTERING_FOR_EXPORT
    }
    return all_models


def get_model_class_and_fields(
    model_name: str,
    qs: models.QuerySet = None,
) -> tuple[models.Model, list[models.Field], list[str], list[str]]:
    """
    Retrieve the model class and its fields given a model name.

    Args:
        model_name (str): The name of the model.

    Returns:
        tuple: A tuple containing the model class, its fields, expected fields, and required fields.

    Raises:
        LookupError: If the specified model does not exist.
    """
    if qs is None:
        model_names_and_classes = get_app_all_exportable_models_with_restriction("apps.")
    else:
        model_names_and_classes = get_app_all_exportable_models("apps.")

    model_class = model_names_and_classes.get(model_name, None)
    if model_class is None:
        raise LookupError(f"No model with name '{model_name}'.")

    # Get all editable and non-auto-created fields of the model
    model_fields = [
        field
        for field in model_class._meta.get_fields(include_parents=True)
        if field.editable and not field.auto_created
    ]

    # Extract verbose names of the fields
    expected_fields = [field.verbose_name.upper() for field in model_fields]

    # Extract verbose names of the required fields
    required_fields = [field.verbose_name.upper() for field in model_fields if not field.null]

    return model_class, model_fields, expected_fields, required_fields


def get_model_field_by_uppercased_verbose_name(
    model_fields: list[models.Field], uppercased_verbose_name: str
) -> models.Field | None:
    """Get model field by verbose name"""
    for field in model_fields:
        if field.verbose_name.upper() == uppercased_verbose_name:
            return field
    return None


def field_value_human_readable(field: models.Field, value: Union[str, list[str]]) -> Union[str, list[str]]:
    """Convert field value to human-readable format"""
    if isinstance(value, list):
        return ",".join([str(item) for item in value])

    if isinstance(field, models.CharField) and field.choices:
        for choice_value, choice_label in field.choices:
            if choice_value == value:
                return choice_label

    if isinstance(field, models.ForeignKey) and value:
        return str(field.related_model.objects.get(pk=value))

    return value


def convert_human_readable_value_to_db_value(
    field: models.Field, human_readable_value: str
) -> Union[str, models.QuerySet]:
    """Convert human-readable value to model value

    Raises ValidationError if human-readable value is not valid
    """
    if isinstance(field, models.CharField) and field.choices:
        for choice_value, choice_label in field.choices:
            if choice_label == human_readable_value:
                return choice_value

    if isinstance(field, models.ForeignKey):
        # str method for importable/exportable models is just the indicator NavAid model which is 3 parts
        parts = [string.strip() for string in human_readable_value.split("-")]
        fields = {}
        if len(parts) == 1:
            fields["indicator"] = parts[0]
        elif len(parts) == 3:
            name, type_display, use_case_display = parts
            type = next(
                choice_value
                for choice_value, choice_label in NavAidType.choices
                if choice_label == type_display
            )
            use_case = next(
                choice_value
                for choice_value, choice_label in NavAidUseCase.choices
                if choice_label == use_case_display
            )
            fields = dict(indicator=name, type=type, use_case=use_case)

        try:
            return field.related_model.objects.get(**fields)
        except Exception:
            raise ValidationError(f"{field.related_model} with {fields} does not exists.")

    if isinstance(field, models.ManyToManyField):
        indicators = [string.strip() for string in human_readable_value.split(",")]
        return field.related_model.objects.filter(indicator__in=indicators)

    return human_readable_value


def validate_excel_data(df: pd.DataFrame, expected_columns: list[str], required_columns: list[str]) -> None:
    """
    Checks if all expected columns are present in the given DataFrame
    and also ensures there are no empty values in any required columns.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to validate.
        expected_columns (list[str]): List of expected column names.
        required_columns (list[str]): List of required column names.

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


def model_to_excel_bytesio(model_name: str, qs: models.QuerySet = None) -> io.BytesIO:
    """Convert model data to Excel file"""
    model_class, model_fields, expected_fields_for_excel, _ = get_model_class_and_fields(model_name, qs)
    exportable_fields = [model_field.name for model_field in model_fields]

    # Retrieve data from the database
    # excel columns have to be field.verbose_name.upper and they'r values should be human readable
    # but model_to_dict dict is a key value pair of model field.name and field.value
    # the logic below is used to change dict key from field.name to field.verbose_name
    field_name_to_vbname = {
        model_field.name: model_field.verbose_name.upper() for model_field in model_fields
    }
    field_name_to_obj = {model_field.name: model_field for model_field in model_fields}

    queryset = qs or model_class.objects.all()

    if queryset.model._meta.model_name == "point":
        queryset = queryset.exclude(navaid__isnull=False)

    data = [
        {
            field_name_to_vbname[field]: field_value_human_readable(field_name_to_obj[field], value)
            for field, value in model_to_dict(instance, fields=exportable_fields).items()
        }
        for instance in queryset
    ]

    # Create a DataFrame from the data
    df = pd.DataFrame(data=data, columns=expected_fields_for_excel)

    # Create a BytesIO object to store the Excel file
    excel_buffer = io.BytesIO()

    # Write the DataFrame to the BytesIO object as an Excel file
    df.to_excel(excel_buffer, index=False)

    return excel_buffer
