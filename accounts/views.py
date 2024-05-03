from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from request.models import Request


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
