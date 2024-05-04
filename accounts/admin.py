from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as BaseGroup
from django.utils import timezone

from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import Group, SubscriptionPlan, User, UserProfile


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
    readonly_fields = ["date_joined"]
    filter_horizontal = [
        "groups",
        "user_permissions",
    ]


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    search_fields = ["duration", "price"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user", "subscription_plan"]
    readonly_fields = ["subscription_end_date"]

    def save_model(self, request, obj, form, change):
        """Override the save_model method to customize behavior when saving a UserProfile instance."""
        # Call the superclass method to perform the default save behavior
        super().save_model(request, obj, form, change)

        # Set subscription_end_date based on selected subscription_plan
        if obj.subscription_plan:
            # Calculate subscription end date based on the chosen plan's duration
            duration_value, duration_unit = obj.subscription_plan.duration.split()
            duration_value = int(duration_value)
            days_in_duration = duration_value * (30 if "month" in duration_unit.lower() else 365)

            obj.subscription_end_date = obj.subscription_start_date + timezone.timedelta(
                days=days_in_duration,
            )
            obj.save()  # Save the UserProfile instance with updated subscription_end_date


# Register the new UserAdmin
admin.site.register(User, UserAdmin)
# Register the Group model from admin.
admin.site.unregister(BaseGroup)
admin.site.register(Group)
