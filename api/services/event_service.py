# CRUD logic for Event
from api.models.event import Event
from api.models.pet import Pet
from api.serializers.pet_serializer import _to_object_id
from datetime import datetime, date

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

_DATETIME_FALLBACK_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
]


def translate_payload(data):
    if isinstance(data, dict):
        return {_CAMEL_TO_SNAKE.get(k, k): translate_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [translate_payload(item) for item in data]
    return data


def parse_payload_dates(data):
    date_fields = ['date', 'follow_up_date']
    if isinstance(data, dict):
        for key, value in data.items():
            if key in date_fields and value is not None and isinstance(value, str):
                data[key] = _parse_datetime_value(key, value)
            else:
                parse_payload_dates(value)
    elif isinstance(data, list):
        for item in data:
            parse_payload_dates(item)
    return data


def _parse_datetime_value(field_name: str, raw_value: str):
    value = (raw_value or "").strip()
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        pass

    for fmt in _DATETIME_FALLBACK_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Invalid {field_name} format. Expected ISO datetime (for example "
        f"'2026-03-20T14:30:00Z') or date formats YYYY-MM-DD / DD/MM/YYYY."
    )


def _date_part(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _ensure_event_date_not_before_birth(pet_id, event_date):
    if not pet_id or not event_date:
        return
    pet = Pet.objects.get(id=_to_object_id(pet_id))
    event_day = _date_part(event_date)
    birth_day = _date_part(getattr(pet, "birth_date", None))
    if event_day is not None and birth_day is not None and event_day < birth_day:
        raise ValueError(f"Event date cannot be before pet birth date ({birth_day.isoformat()}).")


def create_event(user, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    data["owner_id"] = user.id
    pet_id = data.get("pet_id")
    if str(pet_id) not in [str(pid) for pid in (user.pets or [])]:
        raise PermissionError("Not authorized to create events for this pet")
    _ensure_event_date_not_before_birth(pet_id, data.get("date"))
    event = Event.objects.create(**data)
    return Event.objects.get(id=event.id)


def list_events(filters=None):
    if filters:
        return Event.objects.filter(**filters)
    return Event.objects.all()


def list_events_for_pets(pet_ids: list):
    """Returns all events whose pet_id is in the given list of pet_ids."""
    if not pet_ids:
        return Event.objects.none()
    return Event.objects.filter(pet_id__in=pet_ids)


def get_event(event_id):
    return Event.objects.get(id=event_id)


def update_event(event_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    event = Event.objects.get(id=event_id)
    next_pet_id = data.get("pet_id", event.pet_id)
    next_date = data.get("date", event.date)
    _ensure_event_date_not_before_birth(next_pet_id, next_date)
    for key, value in data.items():
        if key == "owner_id":
            continue
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
