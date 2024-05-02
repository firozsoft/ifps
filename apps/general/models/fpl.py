from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from core.utils import validators
from core.utils.choices import FlightRules, FlightType, WeakturbulenceCategory


class FlightPlan(models.Model):
    """The model to be used to valdidate and store flight plan data."""

    addresses = models.TextField(
        validators=[validators.aftn_addresses_validator],
        blank=True,
    )
    filling_time = models.DateTimeField(
        default=timezone.now,
    )
    originator = models.CharField(
        max_length=8,
        validators=[validators.aftn_address_validator],
    )
    aircraft_identification = models.CharField(
        max_length=7,
        validators=[validators.aircraft_identification_validator],
    )
    flight_rules = models.CharField(
        max_length=1,
        choices=FlightRules.choices,
    )
    type_of_flight = models.CharField(
        max_length=1,
        choices=FlightType.choices,
    )
    number_of_aircraft = models.PositiveSmallIntegerField(
        default=1,
        validators=[MaxValueValidator(99)],
        null=True,
        blank=True,
    )
    type_of_aircraft = models.CharField(
        max_length=4,
        validators=[validators.type_of_aircraft_validator],
    )
    weakturbulence_category = models.CharField(
        max_length=1,
        choices=WeakturbulenceCategory.choices,
    )
    equipments_and_capacities = models.CharField(
        max_length=250,
        validators=[validators.equipments_and_capacities_validators],
    )
    departure_aerodrome = models.CharField(
        max_length=4,
        validators=[validators.aerodrome_validator],
    )
    departure_time = models.TimeField()
    cruising_speed = models.CharField(
        max_length=5,
        validators=[validators.speed_validator],
    )
    cruising_level = models.CharField(
        max_length=5,
        validators=[validators.level_validator],
    )
    route = models.TextField()
    destination_aerodrome = models.CharField(
        max_length=4,
        validators=[validators.aerodrome_validator],
    )
    teet = models.CharField(
        verbose_name="TEET",
        max_length=4,
        validators=[validators.teet_validator],
    )
    alternate_aerodrome = models.CharField(
        max_length=4,
        validators=[validators.aerodrome_validator],
    )
    second_alternate_aerodrome = models.CharField(
        max_length=4,
        null=True,
        blank=True,
        validators=[validators.aerodrome_validator],
    )
    other_information = models.TextField()
    date_of_flight = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Flight Plan"
        verbose_name_plural = "Flight Plans"

    def __str__(self):
        return self.aircraft_identification
