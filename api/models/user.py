from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField

#Authentication is handled by Firebase, so we only store the Firebase UID and related info here. No passwords or Django auth models are used.
class User(models.Model):
    id = ObjectIdAutoField(primary_key=True)

    # Firebase UID 
    firebase_uid = models.CharField(max_length=128, unique=True)

    pet_ids = ArrayField(
        models.CharField(max_length=24),
        blank=True,
        default=list,
        help_text="Id of the pets that belong to this user"
    )

    name = models.CharField(max_length=150)
    photo_url = models.URLField(blank=True, null=True)

    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.name# User model (Firebase)
