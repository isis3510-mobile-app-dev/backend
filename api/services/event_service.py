# CRUD logic for Event
from api.models.event import Event
from datetime import datetime

# Mapping of camelCase API payload keys → snake_case model field names
_CAMEL_TO_SNAKE = {
    "petId": "pet_id",
    "ownerId": "owner_id",
    "eventType": "event_type",
    "followUpDate": "follow_up_date",
    "attachedDocuments": "attached_documents",
    "documentId": "document_id",
    "fileName": "file_name",
    "fileUri": "file_uri",
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
    date_fields = ['date', 'follow_up_date']

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


def create_event(data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    event = Event.objects.create(**data)
    return Event.objects.get(id=event.id)


def list_events(filters=None):
    if filters:
        return Event.objects.filter(**filters)
    return Event.objects.all()


def get_event(event_id):
    return Event.objects.get(id=event_id)


def update_event(event_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    event = Event.objects.get(id=event_id)
    for key, value in data.items():
        setattr(event, key, value)
    event.save()
    return Event.objects.get(id=event.id)


def delete_event(event_id):
    Event.objects.filter(id=event_id).delete()


def add_document_to_event(event_id, document_data):
    document_data = translate_payload(document_data)
    event = Event.objects.get(id=event_id)
    if event.attached_documents is None:
        event.attached_documents = []
    event.attached_documents.append(document_data)
    event.save()
    return Event.objects.get(id=event.id)
