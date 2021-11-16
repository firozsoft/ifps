from django.db import models

from apps.utils import YesNo
from .abstract import AerodromeProperties


class Curfew(AerodromeProperties):
    emergency = models.BooleanField("Emergency", choices=YesNo, default=True)
    scramble = models.BooleanField("Scramble", choices=YesNo, default=True)
    sm_flight = models.BooleanField("SM Flight", choices=YesNo, default=True)
    hospital = models.BooleanField("Hospital", choices=YesNo, default=True)
    head = models.BooleanField("Head Flight", choices=YesNo, default=True)
    search_and_rescue = models.BooleanField("SAR(search and rescue)", choices=YesNo, default=True)
    fire_fighting = models.BooleanField("Fire-Fighting", choices=YesNo, default=True)
    hazardous_material_carrier = models.BooleanField("Hazardous Materials", choices=YesNo, default=True)
    medical_evacuation = models.BooleanField("Medical Evacuation", choices=YesNo, default=True)
    delayed_sch_flight = models.BooleanField("Delayed Schedule Flight", choices=YesNo, default=True)
    military_il76 = models.BooleanField("Military IL76", choices=YesNo, default=True)
    on_request = models.BooleanField("OnRequest", choices=YesNo, default=True)

    class Meta(AerodromeProperties.Meta):
        verbose_name = "Curfew"
        verbose_name_plural = "Curfews"
