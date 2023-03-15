from django.urls import path

from . import views

urlpatterns = [
    path("add-data/", views.fill_database),
    path("", views.scrutinization, name="fpl-scrutinization"),
]
