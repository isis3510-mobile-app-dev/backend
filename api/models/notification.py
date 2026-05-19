from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ObjectIdField
from .custom_fields import SafeObjectIdField


class Notification(models.Model):
    """Standalone Notification model."""
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    user_id = SafeObjectIdField()

    type = models.CharField(max_length=100)
    header = models.CharField(max_length=255)
    text = models.TextField()
    action_label = models.CharField(max_length=100, blank=True)
    action_phone = models.CharField(max_length=30, blank=True)
    action_whatsapp = models.CharField(max_length=30, blank=True)
    action_report_id = models.CharField(max_length=40, blank=True)
    action_pet_id = models.CharField(max_length=40, blank=True)
    action_pet_name = models.CharField(max_length=120, blank=True)
    action_pet_photo_url = models.URLField(max_length=500, blank=True)
    action_reporter_name = models.CharField(max_length=120, blank=True)
    action_location = models.CharField(max_length=500, blank=True)
    action_latitude = models.FloatField(null=True, blank=True)
    action_longitude = models.FloatField(null=True, blank=True)
    date_sent = models.DateTimeField(auto_now_add=True)
    date_clicked = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    date_dismissed = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"

    def __str__(self):
        return f"{self.header} ({self.type})"
