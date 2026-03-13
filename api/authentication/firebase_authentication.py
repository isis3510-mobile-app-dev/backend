from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
from api.models.user import User


class FirebaseAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None  # None 

        token = auth_header.split(" ", 1)[1]

        try:
            decoded = auth.verify_id_token(token, check_revoked=True)
        except auth.RevokedIdTokenError:
            raise AuthenticationFailed("Token revocado")
        except auth.ExpiredIdTokenError:
            raise AuthenticationFailed("Token expirado")
        except auth.InvalidIdTokenError:
            raise AuthenticationFailed("Token inválido")

        uid = decoded["uid"]
        email = decoded.get("email", "")
        name = decoded.get("name", "")
        photo_url = decoded.get("picture", "")

        # get_or_create
        try:
            user = User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            user = User.objects.create(
            firebase_uid=uid,
            email=email,
            name=name,
            photo_url=photo_url,
            initials=_make_initials(name),)

        return (user, token)  # (user, auth) 


def _make_initials(name: str) -> str:
    """'Juan Pérez' → 'JP'"""
    parts = name.strip().split()
    return "".join(p[0].upper() for p in parts if p)[:5]