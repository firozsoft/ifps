from django import forms
from django.utils import timezone

from apps.general.models.aircraft import Aircraft
from apps.general.models.base import BasePoint
from apps.general.models.fpl import FlightPlan


def get__all_type_of_aircraft():
    type_of_aircraft = ["ZZZZ"] + sorted(Aircraft.objects.values_list("type", flat=True))
    return zip(type_of_aircraft, type_of_aircraft)


class BasePointForm(forms.ModelForm):
    class Meta:
        model = BasePoint
        fields = "__all__"

    def clean(self):
        cd = self.cleaned_data
        if cd.get("is_fir_boundary", False) and cd.get("fir", FlightPlan.objects.none()).count() != 2:
            self.add_error("fir", "FIR boundary points must have two FIRs.")
        return super().clean()


class FlightPlanForm(forms.ModelForm):
    departure_time = forms.TimeField(
        input_formats=["%H%M"],
        widget=forms.DateTimeInput(format="%H%M"),
    )
    filling_time = forms.DateTimeField(
        input_formats=["%d%H%M"],
        widget=forms.DateTimeInput(format="%d%H%M"),
        initial=timezone.now,
    )
    date_of_flight = forms.DateTimeField(
        input_formats=["%d%H%M"],
        widget=forms.DateTimeInput(format="%d%H%M"),
        disabled=True,
        required=False,
    )
    type_of_aircraft = forms.ChoiceField(choices=get__all_type_of_aircraft)

    class Meta:
        model = FlightPlan
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["filling_time"].disabled = True
