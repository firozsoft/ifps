from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api/", include("api.urls")),
    path("login/", RedirectView.as_view(url="/accounts/login/")),
    path("logout/", RedirectView.as_view(url="/accounts/logout/")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
