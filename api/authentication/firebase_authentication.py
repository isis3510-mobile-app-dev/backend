from functools import wraps

from django.http import JsonResponse
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
            raise AuthenticationFailed("Token revoked")
        except auth.ExpiredIdTokenError:
            raise AuthenticationFailed("Token expired")
        except auth.InvalidIdTokenError:
            raise AuthenticationFailed("Token invalid")

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
    parts = name.strip().split()
    return "".join(p[0].upper() for p in parts if p)[:5]



def firebase_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Token was not given"}, status=401)

        token = auth_header.split(" ", 1)[1]

        try:
            decoded = auth.verify_id_token(token, check_revoked=True)
        except auth.RevokedIdTokenError:
            return JsonResponse({"error": "Token revoked"}, status=401)
        except auth.ExpiredIdTokenError:
            return JsonResponse({"error": "Token expired"}, status=401)
        except auth.InvalidIdTokenError:
            return JsonResponse({"error": "Token invalid"}, status=401)

        uid = decoded["uid"]

        try:
            user = User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

        request.user = user
        return view_func(request, *args, **kwargs)

    return wrapper

def is_pet_owner(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from bson import ObjectId
        pet_id = kwargs.get("pet_id")

        if pet_id and ObjectId(pet_id) not in request.user.pet_ids:
            return JsonResponse({"error": "The user doesn't have access to this pet"}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper