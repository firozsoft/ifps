from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from import_export import fields, widgets

from apps.general.admin.resources import BaseResource

User = get_user_model()


class LogEntryResource(BaseResource):
    content_type = fields.Field(
        column_name="content_type",
        attribute="content_type",
        widget=widgets.ForeignKeyWidget(ContentType, field="name"),
    )
    actor = fields.Field(
        column_name="actor",
        attribute="actor",
        widget=widgets.ForeignKeyWidget(User, field="username"),
    )

    class Meta:
        model = LogEntry
