from django.contrib import admin

from core.forms import ImportRecordForm
from core.models import ImportRecord

admin.site.site_header = "IFPS Administration"
admin.site.site_title = "IFPS Site Admin"


@admin.register(ImportRecord)
class ImportRecordAdmin(admin.ModelAdmin):
    search_fields = ["user__username", "import_message"]
    list_filter = ["was_successful", "upload_date"]
    readonly_fields = ["was_successful"]
    form = ImportRecordForm

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # optionally set Field attributes here, by adding them to kwargs
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "user":
            # disable extra buttons of a relashion fields
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
            formfield.widget.can_view_related = False
        return formfield

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            # setting the user from the request object
            kwargs["initial"] = request.user
            # making the field readonly
            kwargs["disabled"] = True
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
