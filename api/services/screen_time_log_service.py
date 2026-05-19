# CRUD logic for ScreenTimeLog
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone

from api.models import ScreenTimeLog
from api.services import analytics_utils


def _parse_datetime(value):
    """Convert an ISO string to a datetime object if needed."""
    if isinstance(value, str):
        return _ensure_aware_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
    return _ensure_aware_datetime(value)


def _ensure_aware_datetime(value):
    if value is None or not isinstance(value, datetime):
        return value
    if timezone.is_naive(value):
        return timezone.make_aware(value, dt_timezone.utc)
    return value


def create_log(data):
    data = dict(data)  # Shallow copy to avoid mutating the original
    app_type = data.get("appType", "Kotlin")

    if "userId" in data and data["userId"]:
        data["userId"] = str(analytics_utils.resolve_user_id(data["userId"]) or data["userId"])
    if "screenId" in data and data["screenId"]:
        data["screenId"] = str(analytics_utils.resolve_screen_id(data["screenId"], app_type) or data["screenId"])

    # Parse datetime strings coming from the mobile app
    if "startTime" in data:
        data["startTime"] = _parse_datetime(data["startTime"])
    if "endTime" in data:
        data["endTime"] = _parse_datetime(data["endTime"])

    # Auto-compute totalTime if not provided
    if not data.get("totalTime") and data.get("startTime") and data.get("endTime"):
        delta = data["endTime"] - data["startTime"]
        data["totalTime"] = max(0, int(delta.total_seconds()))

    return ScreenTimeLog.objects.create(**data)


def list_logs(user_id=None, screen_id=None):
    queryset = ScreenTimeLog.objects.all()
    if user_id:
        queryset = queryset.filter(userId=user_id)
    if screen_id:
        queryset = queryset.filter(screenId=screen_id)
    return queryset
