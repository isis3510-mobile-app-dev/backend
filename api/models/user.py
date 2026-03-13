from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField, ObjectIdField
from django.core.validators import RegexValidator

#Authentication is handled by Firebase, so we only store the Firebase UID and related info here. No passwords or Django auth models are used.
class User(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    
    # Firebase UID 
    firebase_uid = models.CharField(max_length=128, unique=True)

    pet_ids = ArrayField(
        ObjectIdField(),
        blank=True,
        default=list,
        help_text="Id of the pets that belong to this user"
    )

    family_group = ArrayField(
        ObjectIdField(),
        blank = True,
        default = list, 
        help_text = "Id of the users in the family group"
    )

    name = models.CharField(max_length=150)
    photo_url = models.URLField(blank=True, null=True)
    initials = models.CharField(max_length=20, null=True, validators=[
            RegexValidator(
                regex=r"^[A-ZÁÉÍÓÚÑ]{1,5}$",
                message="Initials must be on Uppercase (max. 5)",
            )
        ])

    email = models.EmailField(max_length=300, default= "user@email.com")

    phone = models.CharField(max_length=20, blank=True,
                             validators=[
            RegexValidator(
                regex=r"^\+?[0-9\s\-\(\)]{7,20}$",
                message="Invalid phone number",
            )
        ])
    address = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_authenticated(self):
        return True

    def __eq__(self, other):
        if isinstance(other, User):
            return self.firebase_uid == other.firebase_uid
        return NotImplemented

    def __hash__(self):
        return hash(self.firebase_uid)

    def __str__(self):
        return f"{self.name} <{self.email}>"

    def __repr__(self):
        return f"<User firebase_uid={self.firebase_uid!r} email={self.email!r}>"

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["firebase_uid"], name="idx_user_firebase_uid"),
            models.Index(fields=["email"], name="idx_user_email"),
        ]

