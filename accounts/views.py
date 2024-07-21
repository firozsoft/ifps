from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import ListView, YearArchiveView
from request.models import Request

from accounts.models import Payment, UserProfile


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject"
    success_message = (
        "We've emailed you instructions for setting your password, "
        "if an account exists with the email you entered. You should receive them shortly."
        " If you don't receive an email, "
        "please make sure you've entered the address you registered with, and check your spam folder."
    )
    success_url = reverse_lazy("accounts:login")


@login_required
def profile(request):
    user = request.user

    # Define conditional expressions (Q objects) for filtering submissions
    total_submissions_query = Q(user=user)
    wrong_submissions_query = Q(user=user, response=422)
    error_prone_submissions_query = Q(user=user, response=400)

    # Aggregate counts of different types of submissions using a single database query
    submission_counts = Request.objects.filter(user=user, path="/submission/").aggregate(
        total_submissions=Count("id", filter=total_submissions_query),
        wrong_submissions=Count("id", filter=wrong_submissions_query),
        error_prone_submissions=Count("id", filter=error_prone_submissions_query),
    )

    # Create a dictionary to store submission counts
    context = {
        "user": user,
        "total_submissions": submission_counts["total_submissions"],
        "wrong_submissions": submission_counts["wrong_submissions"],
        "error_prone_submissions": submission_counts["error_prone_submissions"],
    }

    return render(request, "pages/profile.html", context=context)


class PaymentsListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = "partials/payments.html"
    context_object_name = "payments"
    paginate_by = 15  # Number of payments per page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = self.get_queryset()
        years = payments.dates("payment_date", "year", order="DESC")
        context["years"] = years
        return context

    def get_queryset(self):
        # Get the current user's profile
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        # Filter payments related to the user's profile
        queryset = user_profile.get_payment_history()
        return queryset.order_by("-payment_date")


class PaymentYearArchiveView(LoginRequiredMixin, YearArchiveView):
    queryset = Payment.objects.all()
    date_field = "payment_date"
    make_object_list = True
    allow_future = True
    template_name = "partials/payment_archive_year.html"
    context_object_name = "payments"
    paginate_by = 15  # Number of payments per page

    def get_queryset(self):
        # Get the current user's profile
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        # Filter payments related to the user's profile
        queryset = user_profile.get_payment_history()
        return queryset.order_by("-payment_date")
