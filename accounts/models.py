from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import Group as BaseGroup
from django.core.mail import send_mail
from django.db import models


class Group(BaseGroup):
    pass


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email, and password."""
        if not email:
            msg = "Users must have an email address"
            raise ValueError(msg)
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True."
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True."
            raise ValueError(msg)

        return self._create_user(email, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)  # noqa:SLF001
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                msg = (
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
                raise ValueError(msg)

        elif not isinstance(backend, str):
            raise TypeError("backend must be a dotted import path string (got %r)." % backend)
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
        help_text="Required. 255 characters or fewer.",
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )
    first_name = models.CharField("first name", max_length=150, null=True, blank=True)
    last_name = models.CharField("last name", max_length=150, null=True, blank=True)
    is_staff = models.BooleanField(
        "staff status",
        default=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    last_login = models.DateTimeField("last login", null=True, blank=True)
    date_joined = models.DateTimeField("date joined", auto_now_add=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text=(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="user_set",
        related_query_name="user",
    )

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs) -> None:
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
