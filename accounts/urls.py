from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import path

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
    # TODO: create a profile view
    path("profile/", lambda _: HttpResponse("OK"), name="profile"),
]
