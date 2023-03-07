from django.contrib import admin


class BasePointAdmin(admin.ModelAdmin):
    # readonly_fields = ["longitude", "latitude", "location"]
    readonly_fields = ["longitude", "latitude"]
