# views/user_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from firebase_admin import auth as firebase_auth

from api.models.user import User
from api.serializers.user_serializer import  UserPublicSerializer, UserSerializer, UserUpdateSerializer



class MeView(APIView):


    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial: bool):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=partial,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        firebase_uid = user.firebase_uid
        try:
            firebase_auth.delete_user(firebase_uid)
        except firebase_auth.UserNotFoundError:
            pass
        except Exception as e:
            return Response(
                {"error": f"Error while trying to delete firebase user: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, firebase_uid: str):
        target = get_object_or_404(User, firebase_uid=firebase_uid)

        # Restricción: solo puedes ver usuarios de tu grupo familiar
        requester_id = str(request.user.id)
        if requester_id not in [str(i) for i in target.family_group] \
                and target.firebase_uid != request.user.firebase_uid:
            return Response(
                {"error": "No tienes acceso a este perfil"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserPublicSerializer(target)
        return Response(serializer.data)