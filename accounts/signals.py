from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=get_user_model())
def create_user_profile(**kwargs):
    if kwargs.get("created", False) and kwargs.get("instance", None):
        UserProfile.objects.create(user=kwargs.get("instance"))
        kwargs.get("instance").userprofile.save()
