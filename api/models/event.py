from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField, EmbeddedModelField, ObjectIdField
from api.models.pet import AttachedDocument


class Event(models.Model):
    """Standalone Event model — medical events for a pet."""
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    pet_id = ObjectIdField(help_text="Reference to the pet this event belongs to")
    owner_id = ObjectIdField(help_text="Reference to the user who owns the pet")

    title = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, help_text="Ex: vaccination, vet visit, grooming")
    date = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    provider = models.CharField(max_length=255, blank=True, help_text="Name of the person that provided the service")
    clinic = models.CharField(max_length=255, blank=True, help_text="Name of the clinic where the event took place")
    description = models.TextField(blank=True, help_text="Additional details about the event")
    follow_up_date = models.DateTimeField(null=True, blank=True, help_text="Date for any follow-up actions")

    attached_documents = ArrayField(
        EmbeddedModelField(AttachedDocument),
        blank=True,
        default=list
    )

    class Meta:
        db_table = "events"

    def __str__(self):
        return f"{self.title} ({self.event_type})"
