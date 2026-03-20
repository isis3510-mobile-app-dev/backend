from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ObjectIdField


class FeatureClicksLog(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1)

    userId = ObjectIdField(help_text="Reference to Users._id")
    routeId = ObjectIdField(help_text="Reference to FeatureRoutes._id")

    timestamp = models.DateTimeField(help_text="When this click event was recorded")
    nClicks = models.IntegerField(default=1, help_text="Number of clicks recorded in this event")
    appType = models.CharField(
        max_length=50,
        help_text="App platform (denormalized), e.g. Kotlin, Flutter"
    )

    class Meta:
        db_table = "feature_clicks_logs"

    def __str__(self):
        return f"ClicksLog user={self.userId} route={self.routeId} clicks={self.nClicks}"
