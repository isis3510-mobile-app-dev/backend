from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField, EmbeddedModelField
from django_mongodb_backend.models import EmbeddedModel


#Embedded Models inside document Pet

class MedicalRecord(EmbeddedModel):
    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField()
    file_url = models.URLField(blank=True, null=True)  # Optional

    class Meta:
        managed = False  # Embeded, doesn't create its own collection


class VaccinationEvent(EmbeddedModel):
    """Evento de vacunación embebido dentro de Pet"""
    vaccine_name = models.CharField(max_length=200)      
    date = models.DateField()
    booster_number = models.PositiveIntegerField(default=1) 

    class Meta:
        managed = False


# Documents



class Pet(models.Model):
    id = ObjectIdAutoField(primary_key=True)

    user_ids = ArrayField(
        models.CharField(max_length=24),
        blank=True,
        default=list,
        help_text="Users list that have this pet"
    )

    # General info
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=100, help_text="Ex: dog, cat, rabbit")
    breed = models.CharField(max_length=100, blank=True)
    weight = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    photo_url = models.URLField(blank=True, null=True)

    behavior_notes = models.TextField(blank=True, help_text="Behavior, special care, etc.")

    # Embedded data
    vaccination_events = ArrayField(
        EmbeddedModelField(VaccinationEvent),
        blank=True,
        default=list
    )
    medical_history = ArrayField(
        EmbeddedModelField(MedicalRecord),
        blank=True,
        default=list
    )


    class Meta:
        db_table = "pets"

    def __str__(self):
        return self.name


class Vaccine(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    characteristics = models.TextField(blank=True)
    application_moment = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: 8 weeks, annual, every 3 years"
    )
    animal_type = models.CharField(
        max_length=100,
        help_text="Ex: dog, cat, rabbit"
    )

    class Meta:
        db_table = "vaccines"

    def __str__(self):
        return f"{self.name} ({self.animal_type})"

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
        return self.name