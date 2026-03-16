from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField


class Feature(models.Model):
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
    appType = models.CharField(
        max_length=50,
        help_text="App platform, e.g. Kotlin, Flutter"
    )

    class Meta:
        db_table = "features"

    def __str__(self):
        return f"{self.name} ({self.appType})"
