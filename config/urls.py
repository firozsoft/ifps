from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("login/", RedirectView.as_view(url="/accounts/login/")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
