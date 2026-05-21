from datetime import datetime, date

from api.models import Pet, Exercise
from api.serializers.pet_serializer import _to_object_id


_CAMEL_TO_SNAKE = {
    "petId": "pet_id",
    "ownerId": "owner_id",
    "startedAt": "started_at",
    "durationMinutes": "duration_minutes",
    "distanceKm": "distance_km",
    "createdAt": "created_at",
    "updatedAt": "updated_at",
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
    if isinstance(data, dict):
        raw = data.get("started_at")
        if isinstance(raw, str):
            data["started_at"] = _parse_datetime_value("startedAt", raw)
    return data


def _parse_datetime_value(field_name, raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass

    for fmt in _DATETIME_FALLBACK_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Invalid {field_name} format.")


def _date_part(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _get_owned_pet(user, pet_id):
    if str(pet_id) not in [str(pid) for pid in (user.pets or [])]:
        raise PermissionError("Not authorized to access this pet's exercises")
    return Pet.objects.get(id=_to_object_id(pet_id))


def _validate_exercise(pet, data):
    duration = data.get("duration_minutes")
    if duration is None:
        raise ValueError("Duration is required.")
    try:
        data["duration_minutes"] = int(duration)
    except (TypeError, ValueError):
        raise ValueError("Duration must be numeric.")
    if data["duration_minutes"] <= 0:
        raise ValueError("Duration must be greater than zero.")

    started_at = data.get("started_at")
    if started_at is None:
        raise ValueError("Started date is required.")

    started_day = _date_part(started_at)
    birth_day = _date_part(getattr(pet, "birth_date", None))
    if started_day is not None and birth_day is not None and started_day < birth_day:
        raise ValueError(f"Exercise date cannot be before pet birth date ({birth_day.isoformat()}).")


def list_exercises(user, pet_id):
    _get_owned_pet(user, pet_id)
    return Exercise.objects.filter(pet_id=_to_object_id(pet_id)).order_by("started_at")


def create_exercise(user, pet_id, data):
    data = parse_payload_dates(translate_payload(data))
    pet = _get_owned_pet(user, pet_id)
    data["pet_id"] = pet.id
    data["owner_id"] = user.id
    _validate_exercise(pet, data)

    created = Exercise.objects.create(**data)
    return Exercise.objects.get(id=created.id)


def get_exercise(user, pet_id, exercise_id):
    _get_owned_pet(user, pet_id)
    return Exercise.objects.get(id=_to_object_id(exercise_id), pet_id=_to_object_id(pet_id))

def update_exercise(user, pet_id, exercise_id, data):
    data = parse_payload_dates(translate_payload(data))
    pet = _get_owned_pet(user, pet_id)
    exercise = Exercise.objects.get(id=_to_object_id(exercise_id), pet_id=pet.id)

    merged = {
        "duration_minutes": data.get("duration_minutes", exercise.duration_minutes),
        "started_at": data.get("started_at", exercise.started_at),
    }
    _validate_exercise(pet, merged)

    for field in ["type", "started_at", "duration_minutes", "intensity", "distance_km", "notes"]:
        if field in data:
            setattr(exercise, field, merged.get(field, data[field]))

    exercise.save()
    return Exercise.objects.get(id=exercise.id)


def delete_exercise(user, pet_id, exercise_id):
    _get_owned_pet(user, pet_id)
    Exercise.objects.filter(id=_to_object_id(exercise_id), pet_id=_to_object_id(pet_id)).delete()
