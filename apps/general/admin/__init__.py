from .aircraft import AircraftAdmin  # noqa
from .fids import FIDSAdmin  # noqa
from .notam import NOTAMAdmin  # noqa
from .fir import FIRAdmin  # noqa

from django.contrib import admin


admin.site.site_header = "IFPS Administration"
admin.site.site_title = "IFPS Site Admin"
