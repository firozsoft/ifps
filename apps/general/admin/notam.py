from django.contrib import admin

from apps.general.models import Notam


@admin.register(Notam)
class NOTAMAdmin(admin.ModelAdmin):
    pass
