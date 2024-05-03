from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="pages/login.html",
            redirect_authenticated_user=True,
            next_page="fpl:fpl-submit",
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("profile/", views.profile, name="profile"),
]
