from django import forms
from django.utils import timezone

from apps.general.models import BasePoint, FlightPlan
from apps.general.models.aircraft import Aircraft


def aircraft_types():
    ac_types = ["ZZZZ"] + sorted(Aircraft.objects.values_list("type", flat=True))
    return zip(ac_types, ac_types)


class BasePointForm(forms.ModelForm):
    class Meta:
        model = BasePoint
        fields = "__all__"

    def clean(self):
        super().clean()
        cd = self.cleaned_data
        if cd["is_fir_boundary"] and cd["fir"].count() < 2:
            self.add_error("fir", "FIR boundary points must have two FIRs.")


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
    type_of_aircraft = forms.ChoiceField(choices=aircraft_types)

    class Meta:
        model = FlightPlan
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["filling_time"].disabled = True
