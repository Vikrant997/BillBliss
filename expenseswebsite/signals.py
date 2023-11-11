"""from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .views import set_default_language

@receiver(post_migrate)
def set_default_language_on_startup(sender, **kwargs):
    # Check if the User model is ready
    if sender.name == 'django.contrib.auth':
        # Get all existing users and set their default language
        for user in User.objects.all():
            set_default_language(user)"""
# signals.py
"""from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User
from .views import set_default_language

@receiver(post_migrate)
def set_default_language_on_startup(sender, **kwargs):
    # Check if the User model is ready
    if sender.name == 'django.contrib.auth':
        # Get all existing users and set their default language
        for user in User.objects.all():
            if set_default_language(user):
                print(f"Default language set for user: {user.username}")
            else:
                print(f"User already has a language preference: {user.username}")"""


