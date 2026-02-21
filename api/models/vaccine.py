# Vaccine model
from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField

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
