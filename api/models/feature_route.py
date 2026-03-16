from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField


class FeatureRoute(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1)

    name = models.CharField(max_length=200)
    originButton = models.CharField(
        max_length=100,
        help_text="buttonId of the originating button (ref: Screens.buttons.buttonId)"
    )
    originScreen = models.CharField(
        max_length=24,
        help_text="Reference to Screens._id"
    )
    endButton = models.CharField(
        max_length=100,
        help_text="buttonId of the ending button (ref: Screens.buttons.buttonId)"
    )
    endScreen = models.CharField(
        max_length=24,
        help_text="Reference to Screens._id"
    )

    class Meta:
        db_table = "feature_routes"

    def __str__(self):
        return self.name
