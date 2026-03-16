from datetime import datetime
from api.models import FeatureExecutionLog


def _parse_datetime(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def create_log(data):
    data = dict(data)

    if "startTime" in data:
        data["startTime"] = _parse_datetime(data["startTime"])
    if "endTime" in data:
        data["endTime"] = _parse_datetime(data["endTime"])

    # Auto-compute totalTime if not provided
    if not data.get("totalTime") and data.get("startTime") and data.get("endTime"):
        delta = data["endTime"] - data["startTime"]
        data["totalTime"] = max(0, int(delta.total_seconds()))

    return FeatureExecutionLog.objects.create(**data)


def list_logs(user_id=None, feature_id=None):
    queryset = FeatureExecutionLog.objects.all()
    if user_id:
        queryset = queryset.filter(userId=user_id)
    if feature_id:
        queryset = queryset.filter(featureId=feature_id)
    return queryset
