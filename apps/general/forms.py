from django import forms

from apps.general.models import BasePoint


class BasePointForm(forms.ModelForm):
    class Meta:
        model = BasePoint
        fields = "__all__"

    def clean(self):
        super().clean()
        cd = self.cleaned_data
        if cd["is_fir_boundary"] and cd["fir"].count() < 2:
            self.add_error("fir", "FIR boundary points must have at least two FIRs")
