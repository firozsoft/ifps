from rest_framework import serializers
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.views import submission


class IsSubscribed(BasePermission):
    def has_permission(self, request, _):
        if request.user and request.user.userprofile.is_subscribed():
            return "Active" in request.user.userprofile.get_subscription_status()
        return False


class FlightPlanSubmissionSerializer(serializers.Serializer):
    message = serializers.CharField(
        max_length=None,
        required=True,
        help_text="The FPL text as transmitted via AFTN",
    )


class FlightPlanSubmissionAPIView(APIView):
    """Takes a Flight Plan (FPL) message for analysis and processing and returns a JSON response."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = FlightPlanSubmissionSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.serializer_class
        kwargs.setdefault(
            "context",
            {
                "request": self.request,
                "format": self.format_kwarg,
                "view": self,
            },
        )
        return serializer_class(*args, **kwargs)

    def post(self, request: Request, *_, **__) -> Response:
        """Handle POST requests to submit a Flight Plan (FPL) message.

        Args:
        ----
            request (Request): The HTTP request object containing the message data.

        Returns:
        -------
            Response: JSON response indicating the result of the submission.

        """
        return submission(request)
