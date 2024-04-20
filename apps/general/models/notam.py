import datetime as dt

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone

from apps.general.models.base import AbstractBaseModel
from core.utils import validators


class NotamManager(models.Manager):
    """Add active filter to objects."""

    def active(self, datetime=None) -> models.QuerySet:
        """All valid NOTAMs for a given date."""
        datetime = datetime or timezone.now()
        return (
            super()
            .get_queryset()
            .filter(is_active=True)
            .filter(
                (models.Q(start_date__lte=datetime) & models.Q(end_date__gte=datetime))
                | (models.Q(start_date__lte=datetime) & models.Q(end_date__isnull=True))
            )
        )


class Notam(AbstractBaseModel):
    number = models.CharField(
        max_length=27,
        unique=True,
        validators=[validators.notam_number_validator, MinLengthValidator(19)],
    )
    q_code = models.CharField(
        max_length=44,
        validators=[validators.notam_qcode_validator, MinLengthValidator(44)],
    )
    item_a = models.CharField(
        max_length=34,
        validators=[validators.notam_item_a_validator],
    )
    item_b = models.CharField(
        max_length=10,
        validators=[validators.notam_item_b_validator],
        help_text="10-digit date-time in the format YYMMDDHHMM[EST] or the literal word 'PERM'",
    )
    item_c = models.CharField(
        max_length=13,
        validators=[validators.notam_item_c_validator],
        help_text="10-digit date-time in the format YYMMDDHHMM[EST] or the literal word 'PERM'",
    )
    item_d = models.CharField(max_length=200, blank=True)
    item_e = models.TextField()
    item_f = models.CharField(max_length=50, validators=[validators.notam_item_f_g_validator], blank=True)
    item_g = models.CharField(max_length=50, validators=[validators.notam_item_f_g_validator], blank=True)

    relevant = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True, editable=False)
    end = models.DateTimeField(null=True, blank=True, editable=False)
    affected_firs = models.ManyToManyField(
        "general.FIR",
        verbose_name="Affected FIRs",
        related_name="notams",
        blank=True,
    )
    affected_aerodrome = models.ForeignKey(
        "aerodromes.Aerodrome",
        verbose_name="Affected Aerodrome",
        related_name="notams",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    affected_points = models.ManyToManyField(
        "points.Point",
        verbose_name="Affected Points",
        related_name="notams",
        blank=True,
    )
    affected_navaids = models.ManyToManyField(
        "points.NavAid",
        related_name="navaid_notam",
        verbose_name="Affected Nav.Aids",
        blank=True,
    )
    affected_sidstars = models.ManyToManyField(
        "routes.SidStar",
        verbose_name="Affected SIDs/STARs",
        related_name="notams",
        blank=True,
    )
    affected_route_sections = models.ManyToManyField(
        "routes.RouteSection",
        verbose_name="Affected Route Sections",
        related_name="notams",
        blank=True,
    )

    objects = NotamManager()

    class Meta:
        ordering = ["number"]
        indexes = [models.Index(fields=["number"])]
        verbose_name = "NOTAM"
        verbose_name_plural = "NOTAMs"

    def __str__(self) -> str:
        return self.number

    @property
    def already_has_been_cancelled(self):
        return self.relevant_set.objects.filter(number__icontains="NOTAMC").exists()

    def clean(self) -> None:
        super().clean()

        for item in ("NOTAMR", "NOTAMC"):
            if item in self.number:
                try:
                    relevant_number = self.number.split(item)[1]
                    self.relevant = Notam.objects.get(number=relevant_number)
                except Notam.DoesNotExist:
                    raise ValidationError(
                        {"number": f"Relevant NOTAM matching number {relevant_number} does not exist."}
                    ) from None
                except Notam.MultipleObjectsReturned as err:
                    raise ValidationError({"number": str(err)}) from None

        item_a = self.item_a.strip()
        if len(item_a.split()) > 1:
            lst = [indicator[2] for indicator in item_a.split() if indicator]
            if len(lst) != len(set(lst)):  # At least on 2-letters appeared twice
                raise ValidationError(
                    {
                        "item_a": "Only one aerodrome may be indicated. "
                        "If more than one aerodrome is involved, separate NOTAM must be issued. "
                        "More than one FIR may be indicated when appropriate.",
                    }
                )

        try:
            self.start = dt.datetime.strptime(self.item_b, "%y%m%d%H%M")
        except Exception:
            raise ValidationError(
                {
                    "item_b": "A ten-digit date-time group (yymmddHHMM) in UTC must be indicated.",
                }
            ) from None

        if self.item_c != "PERM":
            try:
                self.end = dt.datetime.strptime(self.item_c[:10], "%y%m%d%H%M")
            except Exception:
                raise ValidationError(
                    {
                        "item_c": "A ten-digit date-time group (yymmddHHMM) in UTC must be indicated.",
                    }
                ) from None

        if self.end and self.start >= self.end:
            raise ValidationError(
                {
                    "item_b": "Item B(Start date-time) must not be greater than Item C(End date-time).",
                    "item_c": "Item B(Start date-time) must not be greater than Item C(End date-time).",
                }
            )

    def save(self, *args, **kwargs) -> None:
        self.notam_type = None
        for item in ("NOTAMR", "NOTAMC"):
            if item in self.number:
                self.notam_type = item
                break
        if self.relevant.already_has_been_cancelled:
            raise ValidationError({"number": f"Relevant NOTAM {self.relevant} already has been cancelled."})

        updated_fields = ["is_active"]
        if self.notam_type == "NOTAMC":
            self.relevant.already_has_been_cancelled = True
            updated_fields.append("already_has_been_cancelled")
        self.relevant.is_active = False
        self.relevant.save(update_fields=updated_fields)

        return super().save(*args, **kwargs)
