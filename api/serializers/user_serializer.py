from rest_framework import serializers
from api.models.user import User
from bson import ObjectId


class ObjectIdField(serializers.Field):

    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        try:
            return ObjectId(str(data))
        except Exception:
            raise serializers.ValidationError("ObjectId invalid")


class UserSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    pets = serializers.ListField(
        child=ObjectIdField(),
        required=False,
        default=list,
    )
    # Expose snake_case model fields as camelCase JSON keys
    familyGroup = serializers.ListField(
        child=ObjectIdField(),
        source="family_group",
        required=False,
        default=list,
    )
    profilePhoto = serializers.URLField(
        source="profile_photo",
        required=False,
        allow_blank=True,
    )
    firebaseUid = serializers.CharField(source="firebase_uid", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "schema",
            "firebaseUid",
            "name",
            "email",
            "token",
            "phone",
            "address",
            "profilePhoto",
            "initials",
            "pets",
            "familyGroup",
            "createdAt",
            "updatedAt",
        ]
        read_only_fields = [
            "id",
            "firebaseUid",
            "createdAt",
            "updatedAt",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    # Accept profilePhoto in the request body
    profilePhoto = serializers.URLField(
        source="profile_photo",
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = User
        fields = [
            "name",
            "token",
            "phone",
            "address",
            "profilePhoto",
            "initials",
        ]

    def validate_initials(self, value):
        return value.upper()


class UserPublicSerializer(serializers.ModelSerializer):
    profilePhoto = serializers.URLField(source="profile_photo", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "profilePhoto", "initials"]