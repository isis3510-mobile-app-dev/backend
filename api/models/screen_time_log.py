from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField


class ScreenTimeLog(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1)

    userId = models.CharField(max_length=24, help_text="Reference to Users._id")
    screenId = models.CharField(max_length=24, help_text="Reference to Screens._id")

    startTime = models.DateTimeField()
    endTime = models.DateTimeField()
    totalTime = models.IntegerField(
        default=0,
        help_text="Total time spent on the screen in seconds"
    )

    class Meta:
        db_table = "screen_time_logs"

    def __str__(self):
        return f"Log user={self.userId} screen={self.screenId} total={self.totalTime}s"
