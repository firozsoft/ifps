from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as BaseGroup

from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import Group, User


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": [
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ],
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    ]
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["email", "password1", "password2"],
            },
        ),
    ]
    list_display = ["email", "first_name", "last_name", "is_staff"]
    list_filter = ["is_staff", "is_superuser", "is_active", "groups"]
    search_fields = ["first_name", "last_name", "email"]
    ordering = ["email"]
    filter_horizontal = [
        "groups",
        "user_permissions",
    ]


# Register the new UserAdmin
admin.site.register(User, UserAdmin)
# Register the Group model from admin.
admin.site.unregister(BaseGroup)
admin.site.register(Group)
