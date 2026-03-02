# HTTP views for User
from api.services import user_service
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    # Get authenticated user
    def get(self, request):
        user = user_service.get_user_by_uid(request.user.firebase_uid)
        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(user, status=status.HTTP_200_OK)

    # Create user (register with Firebase)
    def post(self, request):
        data = {
            **request.data,
            "firebase_uid": request.user.firebase_uid  # UID comes from token
        }
        user = user_service.create_user(data)
        if not user:
            return Response(
                {"error": "User already exists or invalid data"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(user, status=status.HTTP_201_CREATED)

    # Update authenticated user
    def put(self, request):
        user = user_service.update_user(request.user.firebase_uid, request.data)
        if not user:
            return Response(
                {"error": "User already exists or invalid data"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(user, status=status.HTTP_200_OK)

    # Delete authenticated user
    def delete(self, request):
        deleted = user_service.delete_user(request.user.firebase_uid)
        if not deleted:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)