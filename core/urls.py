from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from core import views

app_name = "fpl"

urlpatterns = [
    path("submission/", views.submission, name="submission"),
    path("fpl-submission/", views.FlightPlanCreateView.as_view(), name="fpl-submission"),
    path("export-model/<model_name>/", views.export_model, name="export_model"),
    path("export-models/<app_label>/", views.export_models, name="export_app_models"),
    path("export-models/", views.export_models, name="export_models"),
    path("", login_required(TemplateView.as_view(template_name="pages/index.html")), name="fpl-submit"),
]
