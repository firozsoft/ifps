from django.contrib import admin

from apps.general.forms import BasePointForm


class BasePointAdmin(admin.ModelAdmin):
    form = BasePointForm
    # readonly_fields = ["longitude", "latitude", "location"]
    readonly_fields = ["longitude", "latitude"]
    list_filter = ["is_active", "is_fir_boundary", "fir"]
