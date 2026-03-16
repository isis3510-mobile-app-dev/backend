# Screen model and embedded documents
from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ArrayField, EmbeddedModelField
from django_mongodb_backend.models import EmbeddedModel

# Monkey patch (same fix as pet.py)
ArrayField.embedded_model = property(lambda self: getattr(self.base_field, 'embedded_model', None))


class Button(EmbeddedModel):
    """Button embedded inside a Screen"""
    buttonId = models.CharField(max_length=100)
    schema = models.IntegerField(default=1)
    name = models.CharField(max_length=200)

    class Meta:
        managed = False  # Embedded, doesn't create its own collection


class Screen(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1)

    name = models.CharField(max_length=200)
    hasAds = models.BooleanField(default=False)
    # avgTimeSpent = models.IntegerField(default=0, help_text="Average time spent on screen in seconds")
    # stdTimeSpent = models.IntegerField(default=0, help_text="Standard deviation of time spent in seconds")
    # nScreenTimeEvents = models.IntegerField(default=0, help_text="Number of screen time events recorded")

    buttons = ArrayField(
        EmbeddedModelField(Button),
        blank=True,
        default=list
    )

    class Meta:
        db_table = "screens"

    def __str__(self):
        return self.name
