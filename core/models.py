import os
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.db import models

from core.utils.helpers import zipfile_extactor


def validate_file_size(value):
    if value.size > 10 * 1024 * 1024:  # 10 Megabytes
        raise ValidationError("File size must be less than 10MB")
    try:
        if not value.file.content_type.startswith("application/zip"):
            raise ValidationError("Only ZIP files are allowed")
    except AttributeError:
        if not value.content_type.startswith("application/zip"):
            raise ValidationError("Only ZIP files are allowed")


def generate_upload_path(instance, filename):
    # Generate a dynamic directory path based on the current date and the username
    today = datetime.now()
    username = instance.user.username
    return f"{username}/{today.year}/{today.month}/{today.day}/{today.time().strftime('%H%M%S')}/{filename}"


class ImportRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    file = models.FileField(upload_to=generate_upload_path, max_length=100, validators=[validate_file_size])
    was_successful = models.BooleanField(default=False)
    import_message = models.TextField(blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Import Record"
        verbose_name_plural = "Import Records"

    def __str__(self):
        return f"Import by {self.user.username} on {self.upload_date.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        extract_dir = Path(f"{os.path.dirname(self.file.path)}/extract")
        try:
            zipfile_extactor(self.file.path, extract_dir)
            call_command("update_database", resources=extract_dir)
        except Exception as err:
            self.delete()
            raise err

    def delete(self, *args, **kwargs):
        # Delete the associated file before deleting the instance
        default_storage.delete(self.file.path)
        super().delete(*args, **kwargs)
