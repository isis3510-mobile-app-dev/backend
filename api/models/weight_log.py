from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ObjectIdField


class WeightLog(models.Model):
    """Standalone weight log for a pet, used by Sprint 3 BQ analytics."""

    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1, help_text="Version of the document schema")

    pet_id = ObjectIdField(help_text="Reference to the pet this weight belongs to")
    owner_id = ObjectIdField(help_text="Reference to the user who logged the weight")

    weight = models.FloatField()
    logged_at = models.DateTimeField()
    client_mutation_id = models.CharField(max_length=120, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weight_logs"

    def __str__(self):
        return f"{self.pet_id}: {self.weight}kg at {self.logged_at}"
