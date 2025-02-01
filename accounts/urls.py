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
    path("password-reset/", views.ResetPasswordView.as_view(), name="password_reset"),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("payments/", views.PaymentsListView.as_view(), name="payments_list"),
    path(
        "payments/archive/year/<int:year>/",
        views.PaymentYearArchiveView.as_view(),
        name="payment_archive_year",
    ),
]
