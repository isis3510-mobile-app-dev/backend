from datetime import datetime
from api.models import FeatureClicksLog


def _parse_datetime(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def create_log(data):
    data = dict(data)

    if "timestamp" in data:
        data["timestamp"] = _parse_datetime(data["timestamp"])

    return FeatureClicksLog.objects.create(**data)


def list_logs(user_id=None, route_id=None):
    queryset = FeatureClicksLog.objects.all()
    if user_id:
        queryset = queryset.filter(userId=user_id)
    if route_id:
        queryset = queryset.filter(routeId=route_id)
    return queryset
