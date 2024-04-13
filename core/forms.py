from django import forms

from core.models import ImportRecord, validate_file_size


class ImportRecordForm(forms.ModelForm):
    class Meta:
        model = ImportRecord
        fields = "__all__"

    def clean_file(self):
        file = self.cleaned_data["file"]
        validate_file_size(file)
        return file
