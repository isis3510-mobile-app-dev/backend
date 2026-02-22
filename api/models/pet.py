# Pet model and embedded documents
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
