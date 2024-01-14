# forms.py
from django import forms
from django.core.exceptions import ValidationError

MAX_FILE_SIZE_MB = 10  # Maximum file size in megabytes

VALID_FILENAMES = [
    "Aerodrome.xlsx",
    "Point.xlsx",
    "NavAid.xlsx",
    "Route.xlsx",
    "SidStar.xlsx",
    "OperationalHour.xlsx",
    "RouteScheme.xlsx",
]


def validate_file_size(value):
    limit = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    if value.size > limit:
        raise ValidationError(f"File size exceeds the limit of {MAX_FILE_SIZE_MB} MB.")


def validate_file_name(value):
    valid_file_names = VALID_FILENAMES  # List of allowed file names
    if value.name not in valid_file_names:
        raise forms.ValidationError(f"Only {', '.join(valid_file_names)} files are allowed.")


class FileUploadForm(forms.Form):
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
        validators=[validate_file_name, validate_file_size],
    )
