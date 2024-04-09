# from django.contrib.gis.geos import GEOSGeometry
from argparse import ArgumentParser
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from openpyxl import load_workbook

from apps.general.models.base import BasePoint
from apps.general.utils.helpers import dms_to_decimal_degrees
from core.utils.helpers import (
    get_model_class_and_fields,
    process_excel_sheet_data,
    validate_excel_sheet_data,
)


class Command(BaseCommand):
    help = (
        "Drops the database and rebuilt it using data from Excel files in a given directory. "
        "If no directory provided, defaults to the 'resources' directory. "
        "The Excel file name must match the all lowercased model name with a .xlsx extension."
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

    def handle(self, *args, **kwargs):
        resources_dir: Path = kwargs.get("resources")

        # Validate resources directory
        if not resources_dir.exists():
            raise CommandError("The specified resources directory does not exist.")

        # Determine model names to update
        model_names = [filename.stem for filename in resources_dir.glob("*.xlsx")]

        # Validate model names and Excel file existence
        for model_name in model_names:
            if model_name not in self.importable_model_names:
                raise CommandError(f"'{model_name.upper()}' is not a valid model name.")

        for model_name in self.importable_model_names:
            if not (resources_dir / f"{model_name}.xlsx").exists():
                raise CommandError(f"The Excel file for model '{model_name.upper()}' does not exist.")

        # Sort model names based on predefined order
        sorted_model_names = sorted(model_names, key=lambda item: self.importable_model_names.index(item))

        # Handle rebuild option
        self.stdout.write(self.style.WARNING("Deleting existing data..."))
        for model_name in sorted_model_names:
            model_class, model_fields, expected_fields, required_fields = get_model_class_and_fields(
                model_name
            )

            if model_name == "point":
                model_class.objects.exclude(navaid__isnull=False).delete()
            else:
                model_class.objects.all().delete()

            self.stdout.write(f"Loading data for {model_name}s...")
            # Load data from Excel
            wb = load_workbook(resources_dir / f"{model_name}.xlsx", read_only=True)
            sheet = wb.active

            # Validate the Excel data
            self.stdout.write(f"Validating the Excel data for {model_name}s...")
            try:
                validate_excel_sheet_data(sheet, expected_fields, required_fields)
            except ValidationError as err:
                raise CommandError(str(err))

            # Convert data into model instances
            instances_data, m2m_fields, data_was_error_prone = process_excel_sheet_data(
                sheet, model_fields, self.stderr.write
            )

            if data_was_error_prone:
                raise CommandError(f"The provided data for {model_name.upper()} is not valid(1).")

            model_instances: list[models.Model] = []
            for instance_data in instances_data:
                try:
                    new_instance: models.Model = model_class(**instance_data)
                    new_instance.full_clean()
                except ValidationError as err:
                    data_was_error_prone = True
                    self.stderr.write(str(err))
                else:
                    if isinstance(new_instance, BasePoint):
                        new_instance.latitude, new_instance.longitude = dms_to_decimal_degrees(
                            new_instance.coordinate
                        )
                    model_instances.append(new_instance)

            if data_was_error_prone:
                raise CommandError(f"The provided data for {model_name.upper()} is not valid(2).")

            # Perform bulk update or create
            with transaction.atomic():
                self.stdout.write(f"Initiated bulk creation of {model_name}s...")
                saved_model_instances: list[models.Model] = []
                try:
                    saved_model_instances = model_class.objects.bulk_create(model_instances)
                except ValueError as e:
                    # Check if the ValueError is due to bulk_create not supporting inherited models
                    if "bulk create" in str(e) and "inherited" in str(e):
                        # Fall back to creating each instance individually using save()
                        for instance in model_instances:
                            try:
                                instance.save()
                                saved_model_instances.append(instance)
                            except Exception as save_exception:
                                # Handle save exceptions if needed
                                self.stderr.write(f"Error saving instance: {instance} -> {save_exception}")
                                data_was_error_prone = True
                        if data_was_error_prone:
                            raise CommandError(f"The provided data for {model_name.upper()} is not valid(3).")
                    else:
                        # Handle other types of ValueError
                        raise CommandError(f"Unhandled ValueError: {e}")

                # Handling ManyToMany relation for BasePoint subinstances
                # only one M2M relation exitsts which for BasePoint subclasses to FIR
                if isinstance(model_class(), BasePoint):
                    for instance in saved_model_instances:
                        if instance.indicator in m2m_fields:
                            instance.fir.add(*m2m_fields[instance.indicator])

                self.stdout.write(self.style.SUCCESS(f"Finished creation of {model_name}s."))
        # Output success message
        self.stdout.write("-" * 20)
        self.stdout.write(self.style.SUCCESS("Data has been uploaded successfully."))
