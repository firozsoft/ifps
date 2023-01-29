from django.urls import path

from .views import scrutinization

urlpatterns = [
    path("", scrutinization),
]
