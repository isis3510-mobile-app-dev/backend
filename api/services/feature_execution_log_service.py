from datetime import datetime
from bson import ObjectId
from api.models import FeatureExecutionLog


def _parse_datetime(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError("startTime/endTime must be ISO 8601 strings") from e
    return value


def _parse_int(value, field_name):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{field_name} must be an integer") from e


def _to_object_id(val, field_name):
    if val is None:
        return None
    if isinstance(val, ObjectId):
        return val
    if isinstance(val, str):
        try:
            return ObjectId(val)
        except Exception as e:
            raise ValueError(f"{field_name} must be a valid ObjectId string") from e
    return val


def create_log(data):
    data = dict(data)

    if "startTime" in data:
        data["startTime"] = _parse_datetime(data["startTime"])
    if "endTime" in data:
        data["endTime"] = _parse_datetime(data["endTime"])

    if "totalTime" in data:
        data["totalTime"] = _parse_int(data["totalTime"], "totalTime")
    if "downloadSpeed" in data:
        data["downloadSpeed"] = _parse_int(data["downloadSpeed"], "downloadSpeed")
    if "uploadSpeed" in data:
        data["uploadSpeed"] = _parse_int(data["uploadSpeed"], "uploadSpeed")

    if "userId" in data and data["userId"] is not None:
        data["userId"] = _to_object_id(data["userId"], "userId")
    if "featureId" in data and data["featureId"] is not None:
        data["featureId"] = _to_object_id(data["featureId"], "featureId")

    # Auto-compute totalTime if not provided
    if data.get("totalTime") is None and data.get("startTime") and data.get("endTime"):
        delta = data["endTime"] - data["startTime"]
        data["totalTime"] = max(0, int(delta.total_seconds()))

    return FeatureExecutionLog.objects.create(**data)


def list_logs(user_id=None, feature_id=None):
    queryset = FeatureExecutionLog.objects.all()
    if user_id:
        queryset = queryset.filter(userId=_to_object_id(user_id, "userId"))
    if feature_id:
        queryset = queryset.filter(featureId=_to_object_id(feature_id, "featureId"))
    return queryset
