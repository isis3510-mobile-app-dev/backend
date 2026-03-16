from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ObjectIdField


class Notification(models.Model):
    """Standalone Notification model."""
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    user_id = ObjectIdField()

    type = models.CharField(max_length=100)
    header = models.CharField(max_length=255)
    text = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)
    date_clicked = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications"

    def __str__(self):
        return f"{self.header} ({self.type})"
