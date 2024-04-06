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

        container_dict = {}
        # Handle rebuild option
        self.stdout.write(self.style.WARNING("Deleting existing data..."))
        for model_name in sorted_model_names:
            # NOTE: Deletion of Point instances will delete all NavAid instances too!
            model_class, model_fields, expected_fields, required_fields = get_model_class_and_fields(
                model_name
            )
            model_class.objects.all().delete()
            container_dict[model_name] = [model_class, model_fields, expected_fields, required_fields]

        for model_name in sorted_model_names:
            self.stdout.write(f"Loading data for {model_name}s...")
            # Load data from Excel into a Pandas DataFrame
            excel_data = pd.read_excel(resources_dir / f"{model_name}.xlsx")

            # Validate the Excel data
            self.stdout.write(f"Validating the Excel data for {model_name}s...")
            model_class, model_fields, expected_fields, required_fields = container_dict[model_name]
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
                            # only one M2M relation exitsts which for BasePoint subclasses to FIR
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
                self.stdout.write(f"Initiated bulk creation of {model_name}s...")
                if model_name != "navaid":
                    model_instances = model_class.objects.bulk_create(model_instances)
                else:
                    new_model_instances = []
                    for instance in model_instances:
                        instance.save()
                        new_model_instances.append(instance)
                    model_instances = new_model_instances

                # Handling ManyToMany relation for BasePoint subinstances
                # only one M2M relation exitsts which for BasePoint subclasses to FIR
                if isinstance(model_class(), BasePoint):
                    for instance in model_instances:
                        if instance.indicator in m2m_fields:
                            instance.fir.add(*m2m_fields[instance.indicator])

                self.stdout.write(self.style.SUCCESS(f"Finished creation of {model_name}s."))
        # Output success message
        self.stdout.write("-" * 20)
        self.stdout.write(self.style.SUCCESS("Data has been uploaded successfully."))
