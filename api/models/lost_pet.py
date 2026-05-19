from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField, EmbeddedModelField
from django_mongodb_backend.models import EmbeddedModel

from .custom_fields import SafeObjectIdField


class EmergencyContact(EmbeddedModel):
    """Contact information an owner chooses to expose on a lost pet report."""

    name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    relationship = models.CharField(max_length=80, blank=True)
    expose_phone = models.BooleanField(default=False)
    expose_whatsapp = models.BooleanField(default=False)
    preferred = models.BooleanField(default=False)


class LostPetReport(models.Model):
    """Active or resolved lost-pet state for a Pet."""

    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    pet_id = SafeObjectIdField(help_text="Reference to the pet this report belongs to")
    owner_id = SafeObjectIdField(help_text="Reference to the user that opened the report")

    status = models.CharField(max_length=30, default="active", help_text="active or resolved")
    lost_note = models.TextField(blank=True)
    last_seen_location = models.CharField(max_length=500, blank=True)
    last_seen_latitude = models.FloatField(null=True, blank=True)
    last_seen_longitude = models.FloatField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    expose_medical_info = models.BooleanField(default=False)
    nfc_notifications_enabled = models.BooleanField(default=True)

    emergency_contacts = ArrayField(
        EmbeddedModelField(EmergencyContact),
        blank=True,
        default=list,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lost_pet_reports"
        indexes = [
            models.Index(fields=["pet_id"], name="idx_lost_report_pet"),
            models.Index(fields=["status"], name="idx_lost_report_status"),
        ]

    def __str__(self):
        return f"LostPetReport({self.pet_id}, {self.status})"


class LostPetSighting(models.Model):
    """Location update submitted when someone scans a lost pet NFC tag."""

    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    report_id = SafeObjectIdField(help_text="Reference to the lost pet report")
    pet_id = SafeObjectIdField(help_text="Reference to the pet sighted")

    seen_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=500, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    note = models.TextField(blank=True)
    photo_url = models.URLField(max_length=2000, blank=True, null=True)

    reporter_name = models.CharField(max_length=150, blank=True)
    reporter_phone = models.CharField(max_length=30, blank=True)
    reporter_email = models.EmailField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lost_pet_sightings"
        indexes = [
            models.Index(fields=["report_id"], name="idx_sighting_report"),
            models.Index(fields=["pet_id"], name="idx_sighting_pet"),
        ]

    def __str__(self):
        return f"LostPetSighting({self.report_id})"
