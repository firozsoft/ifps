# from django.contrib.gis.geos import GEOSGeometry
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction

from apps.general.models.base import BasePoint
from apps.general.utils.helpers import dms_to_decimal_degrees
from core.utils.helpers import (
    convert_human_readable_value_to_db_value,
    get_model_class_and_fields,
    get_model_field_by_uppercased_verbose_name,
    validate_excel_data,
)


class Command(BaseCommand):
    help = (
        "Updates the database using data from Excel files in a given directory. "
        "If no directory provided, defaults to the 'resources' directory. "
        "Optionally, specify one or more model names to update. "
        "If no model name provided, all models will be updated. "
        "The Excel file name must match the model name with a .xlsx extension."
    )

    importable_model_names = (
        # The order in this tuple is important
        "fir",
        "aerodrome",
        "dailyoperationalhour",
        "temporaryclosure",
        "curfew",
        "navaid",
        "point",
        "sidstar",
        "routesection",
        "routescheme",
    )

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--resources",
            type=Path,
            nargs="?",
            help='Directory containing Excel files. Defaults to "./resources".',
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

        # Validate resources directory
        if not resources_dir.exists():
            raise CommandError("The specified resources directory does not exist.")

        # Determine model names to update
        model_names = models_to_update or [filename.stem for filename in resources_dir.glob("*.xlsx")]

        # Validate model names and Excel file existence
        for model_name in model_names:
            if model_name not in self.importable_model_names:
                raise CommandError(f"'{model_name.upper()}' is not a valid model name.")

            if not (resources_dir / f"{model_name}.xlsx").exists():
                raise CommandError(f"The Excel file for model '{model_name.upper()}' does not exist.")

        # Sort model names based on predefined order
        model_names = sorted(model_names, key=lambda item: self.importable_model_names.index(item))

        # Handle rebuild option
        if rebuild:
            self.stdout.write(self.style.WARNING("Deleting existing data..."))
            for model_name in model_names:
                model, _, _, _ = get_model_class_and_fields(model_name)
                model.objects.all().delete()

        # Update or create model instances
        for model_name in model_names:
            self.stdout.write(f"Loading data for {model_name}s...")
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
            m2m_fields = {}
            for _, row in excel_data.iterrows():
                instance_data = {}
                for field_uppercased_verbose_name, value in row.items():
                    field = get_model_field_by_uppercased_verbose_name(
                        model_fields, field_uppercased_verbose_name
                    )
                    # Convert human-readable value to model value
                    try:
                        if isinstance(field, models.ManyToManyField):
                            if "INDICATOR" in row:
                                m2m_fields[row["INDICATOR"]] = convert_human_readable_value_to_db_value(
                                    field, value
                                )
                        else:
                            instance_data[field.name] = convert_human_readable_value_to_db_value(field, value)
                    except ValidationError as err:
                        data_was_error_prone = True
                        self.stderr.write(str(err))
                try:
                    new_instance: models.Model = model_class(**instance_data)
                    if isinstance(new_instance, BasePoint):
                        new_instance.latitude, new_instance.longitude = dms_to_decimal_degrees(
                            new_instance.coordinate
                        )
                    new_instance.full_clean()
                    model_instances.append(new_instance)
                except ValidationError as err:
                    data_was_error_prone = True
                    self.stderr.write(str(err))

            if data_was_error_prone:
                raise CommandError(f"The provided data for {model_name.upper()} is not valid.")

            # Perform bulk update or create
            with transaction.atomic():
                if rebuild:
                    self.stdout.write(self.style.NOTICE(f"Initiated bulk creation of {model_name}s..."))
                    if model_name != "navaid":
                        model_instances = model_class.objects.bulk_create(model_instances)
                    else:
                        new_model_instances = []
                        for instance in model_instances:
                            instance.save()
                            new_model_instances.append(instance)
                        model_instances = new_model_instances
                    if isinstance(model_class(), BasePoint):
                        for instance in model_instances:
                            if instance.indicator in m2m_fields:
                                instance.fir.add(*m2m_fields[instance.indicator])

                    self.stdout.write(self.style.SUCCESS(f"Finished creation of {model_name}s..."))
                else:
                    self.stdout.write(self.style.NOTICE(f"Initiated bulk update of {model_name}s..."))
                    model_class.objects.bulk_update(model_instances, model_fields)
                    self.stdout.write(self.style.SUCCESS(f"Finished updating {model_name}s..."))

        # Output success message
        self.stdout.write("-" * 20)
        if rebuild:
            self.stdout.write(self.style.SUCCESS("Data has been rebuilt successfully."))
        else:
            self.stdout.write(self.style.SUCCESS("Data has been updated successfully."))
