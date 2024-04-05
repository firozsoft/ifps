from django import template
from django.db import models

from core.utils.helpers import MODELS_REQUIRING_FILTERING_FOR_EXPORT, get_app_all_exportable_models

register = template.Library()


@register.filter
def is_exportable(obj):
    model: models.Model = obj["model"]
    model_name = model._meta.model_name
    model_names_and_classes = get_app_all_exportable_models("apps.")
    return model_name in model_names_and_classes and model_name not in MODELS_REQUIRING_FILTERING_FOR_EXPORT
