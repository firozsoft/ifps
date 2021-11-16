from django.contrib import admin

from apps.general.models import Fids


@admin.register(Fids)
class FIDSAdmin(admin.ModelAdmin):
    pass
