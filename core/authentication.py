from django.conf import settings
from django.core import signing
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from core.models import APISession

TOKEN_SALT = "djangoportal.api-session"


def issue_token(session):
    return signing.dumps({"session": str(session.pk)}, salt=TOKEN_SALT, compress=True)


class APISessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != b"bearer":
            raise AuthenticationFailed("Invalid authorization header.")
        try:
            payload = signing.loads(parts[1].decode("ascii"), salt=TOKEN_SALT, max_age=settings.API_SESSION_MAX_AGE)
            session = APISession.objects.select_related("user").get(pk=payload["session"])
        except (UnicodeDecodeError, signing.BadSignature, KeyError, APISession.DoesNotExist, ValueError):
            raise AuthenticationFailed("Invalid or expired API session.")
        if not session.active:
            raise AuthenticationFailed("API session is no longer active.")
        return session.user, session

    def authenticate_header(self, request):
        return "Bearer"
