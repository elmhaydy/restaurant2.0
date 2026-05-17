# admin_panel/signals.py
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .utils import create_log


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    create_log(
        request,
        "login",
        "Authentification",
        f"{user.username} s'est connecte"
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    username = getattr(user, "username", None)
    if not username and getattr(request, "user", None) is not None:
        username = getattr(request.user, "username", None)
    if not username:
        username = "Utilisateur inconnu"

    create_log(
        request,
        "logout",
        "Authentification",
        f"{username} s'est deconnecte"
    )
