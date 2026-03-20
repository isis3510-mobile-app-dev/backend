from datetime import datetime
from bson import ObjectId
from api.models import FeatureClicksLog
from api.services import analytics_utils


def _parse_datetime(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError("timestamp must be ISO 8601 string") from e
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

    if "timestamp" in data:
        data["timestamp"] = _parse_datetime(data["timestamp"])
    if "nClicks" in data:
        data["nClicks"] = _parse_int(data["nClicks"], "nClicks")

    app_type = data.get("appType", "Kotlin")
    if "userId" in data and data["userId"] is not None:
        original_u = data["userId"]
        data["userId"] = analytics_utils.resolve_user_id(original_u)
        if not data["userId"]:
            raise ValueError(f"User with firebase_uid '{original_u}' not found. Ensure user is created.")

    if "routeId" in data and data["routeId"] is not None:
        original_r = data["routeId"]
        data["routeId"] = analytics_utils.resolve_route_id(original_r, app_type)
        if not data["routeId"]:
            raise ValueError(f"FeatureRoute '{original_r}' for appType '{app_type}' not found. Please seed analytics data.")

    return FeatureClicksLog.objects.create(**data)


def list_logs(user_id=None, route_id=None):
    queryset = FeatureClicksLog.objects.all()
    if user_id:
        queryset = queryset.filter(userId=_to_object_id(user_id, "userId"))
    if route_id:
        queryset = queryset.filter(routeId=_to_object_id(route_id, "routeId"))
    return queryset
