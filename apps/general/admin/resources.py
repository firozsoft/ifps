import tablib
from import_export import fields, resources, widgets

from apps.general.models.aircraft import Aircraft
from apps.general.models.base import FIR
from apps.general.models.notam import Notam
from core.utils.helpers import SEPARATOR


class BaseResource(resources.ModelResource):
    class Meta:
        skip_unchanged = True
        report_skipped = False
        exclude = ["created", "updated"]

    def get_export_headers(self):
        headers = []
        model_fields = self.Meta.model._meta.get_fields()
        for field in self.get_fields():
            header = next(
                (f.verbose_name.upper() for f in model_fields if f.name == field.column_name),
                field.column_name,
            )
            headers.append(header)
        return headers

    def before_import(self, dataset: tablib.core.Dataset, using_transactions, dry_run, **kwargs):
        model_fields = self.Meta.model._meta.get_fields()
        headers = []
        for header in dataset.headers:
            header = next(
                f.name
                for f in model_fields
                if hasattr(f, "verbose_name") and f.verbose_name.upper() == header
            )
            headers.append(header)
        dataset.headers = headers
        return super().before_import(dataset, using_transactions, dry_run, **kwargs)

    def export_field(self, field, obj):
        if isinstance(field.attribute, str) and hasattr(obj, f"get_{field.attribute}_display"):
            return getattr(obj, f"get_{field.attribute}_display")()
        else:
            return super().export_field(field, obj)

    def before_import_row(self, row, **kwargs):
        for field_name, field_value in row.items():
            model_fields = {field.column_name: field for field in self.get_fields()}
            if field_name in model_fields:
                model_field = model_fields.get(field_name).attribute
                if isinstance(model_field, str) and hasattr(self.Meta.model, f"{model_field}_field_choices"):
                    # Get choices for the field
                    choices = dict(getattr(self.Meta.model, f"{model_field}_field_choices"))
                    # Convert human-readable value to code value
                    for code, human_readable in choices.items():
                        if human_readable == field_value:
                            row[field_name] = code
                            break
        return super().before_import_row(row, **kwargs)


class BasePointResource(BaseResource):
    fir = fields.Field(
        column_name="fir",
        attribute="fir",
        widget=widgets.ManyToManyWidget(FIR, field="indicator", separator=SEPARATOR),
    )

    class Meta:
        import_id_fields = ("id", "indicator")


class AircraftResource(BaseResource):
    class Meta:
        model = Aircraft


class FIRResource(BaseResource):
    class Meta:
        model = FIR
        import_id_fields = ("id", "indicator")


class NotamResource(BaseResource):
    class Meta:
        model = Notam
