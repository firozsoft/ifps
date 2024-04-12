from django import template
from django.db import models

from core.utils.helpers import get_app_exportable_models

register = template.Library()


@register.filter
def is_exportable(obj):
    model: models.Model = obj["model"]
    model_name = model._meta.model_name
    exportable_models = get_app_exportable_models("apps.")
    return model_name in exportable_models
