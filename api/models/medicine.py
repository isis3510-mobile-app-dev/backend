from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ObjectIdField


class Medicine(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    pet_id = ObjectIdField(help_text="Reference to the pet this medicine belongs to")
    owner_id = ObjectIdField(help_text="Reference to the user who owns the pet")

    ADMINISTRATION_ROUTE_CHOICES = [
        ("oral", "oral"),
        ("topical", "topical"),
        ("injectable", "injectable"),
    ]

    DOSAGE_UNIT_CHOICES = [
        ("g", "g"),
        ("mg", "mg"),
        ("ml", "ml"),
        ("tablet", "tablet"),
        ("drops", "drops"),
    ]

    medicine_name = models.CharField(max_length=255)
    administration_route = models.CharField(max_length=20, choices=ADMINISTRATION_ROUTE_CHOICES)
    dosage_value = models.FloatField()
    dosage_unit = models.CharField(max_length=20, choices=DOSAGE_UNIT_CHOICES)
    frequency = models.IntegerField(help_text="Frequency of administration in hours")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    photo_url = models.URLField(max_length=2000, blank=True, null=True)
    reminder_enabled = models.BooleanField(default=False)
    last_administered = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "medicines"

    def __str__(self):
        return f"{self.medicine_name} ({self.administration_route})"