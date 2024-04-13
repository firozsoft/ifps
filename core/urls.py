from django.urls import path

from . import views

urlpatterns = [
    path("login", views.CustomLoginView.as_view(), name="login"),
    path("submission", views.submission, name="submission"),
    path("fpl-submission", views.FlightPlanCreateView.as_view(), name="fpl-submission"),
    path("export-model/<model_name>", views.export_model, name="export_model"),
    path("export-models/<app_label>", views.export_models, name="export_app_models"),
    path("export-models", views.export_models, name="export_models"),
]
