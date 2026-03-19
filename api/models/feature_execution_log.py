from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField, ObjectIdField


class FeatureExecutionLog(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    schema = models.IntegerField(default=1)

    userId = ObjectIdField(help_text="Reference to Users._id")
    featureId = ObjectIdField(help_text="Reference to Features._id")

    startTime = models.DateTimeField()
    endTime = models.DateTimeField()
    totalTime = models.IntegerField(default=0, help_text="Total execution time in seconds")

    downloadSpeed = models.IntegerField(default=0, help_text="Download speed in kbps at time of execution")
    uploadSpeed = models.IntegerField(default=0, help_text="Upload speed in kbps at time of execution")

    class Meta:
        db_table = "feature_execution_logs"

    def __str__(self):
        return f"ExecLog user={self.userId} feature={self.featureId} total={self.totalTime}s"
