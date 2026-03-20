# CRUD logic for Notification
from api.models.notification import Notification
from datetime import datetime

# Mapping of camelCase API payload keys → snake_case model field names
_CAMEL_TO_SNAKE = {
    "userId": "user_id",
    "dateSent": "date_sent",
    "dateClicked": "date_clicked",
    "isRead": "is_read",
    "isDismissed": "is_dismissed",
    "dateDismissed": "date_dismissed",
}


def translate_payload(data):
    """Recursively translate camelCase API payload keys to snake_case model field names."""
    if isinstance(data, dict):
        return {_CAMEL_TO_SNAKE.get(k, k): translate_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [translate_payload(item) for item in data]
    return data


def parse_payload_dates(data):
    """Convert date strings in the payload to Python datetime objects."""
    date_fields = ['date_sent', 'date_clicked', 'date_dismissed']

    if isinstance(data, dict):
        for key, value in data.items():
            if key in date_fields and value is not None and isinstance(value, str):
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
            else:
                parse_payload_dates(value)
    elif isinstance(data, list):
        for item in data:
            parse_payload_dates(item)

    return data


def create_notification(data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    notification = Notification.objects.create(**data)
    return Notification.objects.get(id=notification.id)


def list_notifications(filters=None):
    if filters:
        return Notification.objects.filter(**filters)
    return Notification.objects.all()


def get_notification(notification_id):
    return Notification.objects.get(id=notification_id)


def update_notification(notification_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    notification = Notification.objects.get(id=notification_id)
    for key, value in data.items():
        setattr(notification, key, value)
    notification.save()
    return Notification.objects.get(id=notification.id)


def delete_notification(notification_id):
    Notification.objects.filter(id=notification_id).delete()
