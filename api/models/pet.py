from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField, EmbeddedModelField
from django_mongodb_backend.models import EmbeddedModel

# --- INICIO DEL MONKEY PATCH (Fix para bug de django-mongodb-backend) ---
# Le enseñamos al ArrayField a buscar el modelo embebido dentro de su campo base.
ArrayField.embedded_model = property(lambda self: getattr(self.base_field, 'embedded_model', None))
# --- FIN DEL MONKEY PATCH ---


class AttachedDocument(EmbeddedModel):
    """Documento adjunto embebido dentro de Vaccination y Event"""
    document_id = models.CharField(max_length=24)  # ID of the document in the system
    file_name = models.CharField(max_length=200)
    file_uri = models.URLField(blank=True, null=True)  # URI to access the document


class Event(EmbeddedModel):
    """Evento médico embebido dentro de Pet"""
    event_id = models.CharField(max_length=24)  # ID of the event in the system
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=100, help_text="Ex: vaccination, vet visit, grooming")
    date = models.DateField()
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    provider = models.CharField(max_length=200, blank=True, help_text="Name of the personthat provided the service")
    clinic = models.CharField(max_length=200, blank=True, help_text="Name of the clinic where the event took place")
    description = models.TextField(blank=True, help_text="Additional details about the event")
    follow_up_date = models.DateField(null=True, blank=True, help_text="Date for any follow-up actions or appointments related to this event")

    attached_documents = ArrayField(
        EmbeddedModelField(AttachedDocument),
        blank=True,
        default=list
    )

    
class Vaccination(EmbeddedModel):
    """Evento de vacunación embebido dentro de Pet"""
    vaccine_id = models.CharField(max_length=24)
    date_given = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, blank=True, help_text="Ex: completed, pending, overdue")
    administered_by = models.CharField(max_length=200, blank=True, help_text="Name of the person or clinic that administered the vaccine")

    attached_documents = ArrayField(
        EmbeddedModelField(AttachedDocument),
        blank=True,
        default=list
    )

class Notification(EmbeddedModel):
    """Notificación embebida dentro de Pet"""
    notification_id = models.CharField(max_length=24)  # ID of the notification in the system
    type = models.CharField(max_length=100, help_text="Ex: vaccination reminder, vet appointment")
    header = models.CharField(max_length=200)
    text = models.TextField()
    date_sent = models.DateTimeField()
    date_clicked = models.DateTimeField(null=True, blank=True)

class Pet(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.CharField(max_length=10, default="1.0", help_text="Version of the document schema")

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
    gender = models.CharField(max_length=10, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    weight = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    color = models.CharField(max_length=50, blank=True)
    photo_url = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, help_text="Ex: healthy, needs attention, etc.")
    is_nfc_synced = models.BooleanField(default=False, help_text="Indicates if the pet is synced with NFC tag")
    known_allergies = models.TextField(blank=True, help_text="Known allergies or sensitivities")
    default_vet = models.CharField(max_length=200, blank=True, help_text="Name of the default veterinarian")
    default_clinic = models.CharField(max_length=200, blank=True, help_text="Name of the default clinic")

    # Embedded data
    vaccinations = ArrayField(
        EmbeddedModelField(Vaccination),
        blank=True,
        default=list
    )
    events = ArrayField(
        EmbeddedModelField(Event),
        blank=True,
        default=list
    )

    notifications = ArrayField(
        EmbeddedModelField(Notification),
        blank=True,
        default=list
    )


    class Meta:
        db_table = "pets"

    def __str__(self):
        return self.name
