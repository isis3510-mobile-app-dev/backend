# Vaccine model
from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField

class Vaccine(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1)
    name = models.CharField(max_length=200, default="")
    species = models.JSONField(default=list)  # Array of strings
    product_name = models.CharField(max_length=200, default="")
    manufacturer = models.CharField(max_length=200, default="")
    interval_days = models.IntegerField(default=0)
    description = models.TextField(default="")

    class Meta:
        db_table = "vaccines"

    def __str__(self):
        return f"{self.name} - {self.product_name}"