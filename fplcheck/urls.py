from django.urls import path

from . import views

urlpatterns = [
    path("", views.scrutinization, name="fpl-scrutinization"),
    path("/telegram", views.telegram_bot),
]
