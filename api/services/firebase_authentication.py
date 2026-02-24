from firebase_admin import auth
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from api.models import User

class FirebaseAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None
        
        try: 
            id_token = auth_header.split(" ")[1]
        except IndexError:
            raise AuthenticationFailed("Invalid token format")
        
        try: 
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise AuthenticationFailed("Invalid or expired token")
        
        uid = decoded_token["uid"]
        email = decoded_token.get("email")

        user, created = User.objects.get_or_create(
            firebase_uid = uid
        )
        return (user, None)