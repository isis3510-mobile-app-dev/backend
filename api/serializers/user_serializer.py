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
    pet_ids = serializers.ListField(
        child=ObjectIdField(),
        required=False,
        default=list,
    )
    family_group = serializers.ListField(
        child=ObjectIdField(),
        required=False,
        default=list,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "firebase_uid",
            "name",
            "email",
            "phone",
            "address",
            "photo_url",
            "initials",
            "pet_ids",
            "family_group",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "firebase_uid",
            "created_at",
            "updated_at",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = User
        fields = [
            "name",
            "phone",
            "address",
            "photo_url",
            "initials",
        ]

    def validate_initials(self, value):
        return value.upper()
    

class UserPublicSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "name", "photo_url", "initials"]