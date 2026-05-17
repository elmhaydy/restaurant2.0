from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import User


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_value = username or kwargs.get("username")

        if not login_value or not password:
            return None

        try:
            user = User.objects.get(
                Q(username__iexact=login_value) |
                Q(email__iexact=login_value)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None