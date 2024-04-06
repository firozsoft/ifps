from django.contrib import admin

from apps.general.models.notam import Notam


@admin.register(Notam)
class NOTAMAdmin(admin.ModelAdmin):
    search_fields = ("number",)
    autocomplete_fields = ("relevant",)
