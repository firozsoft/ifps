# from django.contrib.gis.geos import GEOSGeometry
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction

from core.utils.helpers import (
    convert_human_readable_value_to_db_value,
    get_model_class_and_fields,
    get_model_field_by_uppercased_verbose_name,
    validate_excel_data,
)


class Command(BaseCommand):
    help = (
        "Updates the database using data of Excel files from a given directory. "
        "If no directory provided, defaults to resources directory. "
        "Optionally, specify one or more model names to get update. "
        "If no model name provided, all models will get update. "
        "The Excel files name must be only the model name with .xlsx extention."
    )

    importable_model_names = (
        # The order in this tuple is important
        "fir",
        "aerodrome",
        "dailyoperationalhour",
        "temporaryclosure",
        "curfew",
        "point",
        "navaid",
        "sidstar",
        "routesection",
        "routescheme",
    )

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--resources",
            type=Path,
            nargs="?",
            help='A directory that contains Excel files. Default is "./resources" directory.',
            default=Path("resources"),
        )

        group = parser.add_mutually_exclusive_group()

        group.add_argument(
            "--models",
            type=str,
            nargs="*",
            help="Names of the models to update (space-separated).",
            choices=self.importable_model_names,
        )
        group.add_argument(
            "--rebuild",
            action="store_true",
            help="Delete all existing models in the database and build from scratch.",
        )

    def handle(self, *args, **kwargs):
        models_to_update = kwargs.get("models")
        rebuild = kwargs.get("rebuild")
        resources_dir: Path = kwargs.get("resources")

        if not resources_dir.exists():
            raise CommandError("The path to resources does not exists.")

        model_names = models_to_update or [filename.stem for filename in resources_dir.glob("*.xlsx")]

        for model_name in model_names:
            if model_name not in self.importable_model_names:
                raise CommandError(f"Name '{model_name}' is not acceptable Excel/Model name.")

            if not (resources_dir / f"{model_name}.xlsx").exists():
                raise CommandError(f"The Excel file for model '{model_name}' does not exist.")

        model_names = sorted(model_names, key=lambda item: self.importable_model_names.index(item))

        if rebuild:
            # Delete all existing data in the database
            for model_name in model_names:
                model, _ = get_model_class_and_fields(model_name)
                model.objects.delete()

        for model_name in model_names:
            # Load data from Excel into a Pandas DataFrame
            excel_data = pd.read_excel(resources_dir / f"{model_name}.xlsx")

            # Validate the Excel data
            model_class, model_fields, expected_fields, required_fields = get_model_class_and_fields(
                model_name
            )
            try:
                validate_excel_data(excel_data, expected_fields, required_fields)
            except ValidationError as err:
                raise CommandError(str(err))

            # Convert data into model instances
            model_instances = []
            data_was_error_prone = False
            for index, row in excel_data.iterrows():
                instance_data = {}
                for field_uppercased_verbose_name, value in row.items():
                    field = get_model_field_by_uppercased_verbose_name(
                        model_fields, field_uppercased_verbose_name
                    )
                    # Convert human-readable value to model value
                    try:
                        instance_data[field.name] = convert_human_readable_value_to_db_value(field, value)
                        new_instance: models.Model = model_class(**instance_data)
                        new_instance.full_clean()
                        model_instances.append(new_instance)
                    except ValidationError as err:
                        data_was_error_prone = True
                        self.stderr.write(str(err))

            if data_was_error_prone:
                raise CommandError(f"The provided data for {model_name} is not valid.")

            # Perform bulk update or create
            with transaction.atomic():
                model_class.objects.bulk_update_or_create(model_instances, model_fields)
