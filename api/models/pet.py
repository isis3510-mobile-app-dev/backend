from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField, EmbeddedModelField, ObjectIdField
from django_mongodb_backend.models import EmbeddedModel

# --- INICIO DEL MONKEY PATCH (Fix para bug de django-mongodb-backend) ---
# Le enseñamos al ArrayField a buscar el modelo embebido dentro de su campo base.
ArrayField.embedded_model = property(lambda self: getattr(self.base_field, 'embedded_model', None))
# --- FIN DEL MONKEY PATCH ---


class AttachedDocument(EmbeddedModel):
    """Documento adjunto embebido dentro de Vaccination y Event"""
    document_id = ObjectIdField()  # ID of the document in the system
    file_name = models.CharField(max_length=255)
    file_uri = models.URLField(max_length=500, blank=True, null=True)  # URI to access the document


class Vaccination(EmbeddedModel):
    """Evento de vacunación embebido dentro de Pet"""
    vaccine_id = ObjectIdField()
    date_given = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, default="completed", help_text="Ex: completed, pending, overdue")
    administered_by = models.CharField(max_length=255, blank=True, help_text="Name of the person or clinic that administered the vaccine")
    clinic_name = models.CharField(max_length=255, blank=True, help_text="Name of the clinic where the vaccine was administered")
    attached_documents = ArrayField(
        EmbeddedModelField(AttachedDocument),
        blank=True,
        default=list
    )

class Pet(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    owners = ArrayField(
        ObjectIdField(),
        blank=True,
        default=list,
        help_text="Ids of the users that own this pet"
    )

    # General info
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=100, help_text="Ex: dog, cat, rabbit")
    breed = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10)
    birth_date = models.DateField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    color = models.CharField(max_length=50, blank=True)
    photo_url = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=50, default="healthy", help_text="Ex: healthy, needs attention, etc.")
    is_nfc_synced = models.BooleanField(default=False, help_text="Indicates if the pet is synced with NFC tag")
    known_allergies = models.TextField(blank=True, help_text="Known allergies or sensitivities")
    default_vet = models.CharField(max_length=255, blank=True, help_text="Name of the default veterinarian")
    default_clinic = models.CharField(max_length=255, blank=True, help_text="Name of the default clinic")

    # Embedded data
    vaccinations = ArrayField(
        EmbeddedModelField(Vaccination),
        blank=True,
        default=list
    )

    class Meta:
        db_table = "pets"

    def __str__(self):
        return self.name
