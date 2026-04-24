from datetime import datetime, date

from api.models import Pet, WeightLog
from api.serializers.pet_serializer import _to_object_id


_CAMEL_TO_SNAKE = {
    "petId": "pet_id",
    "ownerId": "owner_id",
    "loggedAt": "logged_at",
    "clientMutationId": "client_mutation_id",
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
        raw = data.get("logged_at")
        if isinstance(raw, str):
            data["logged_at"] = _parse_datetime_value("loggedAt", raw)
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
        raise PermissionError("Not authorized to access this pet's weight logs")
    return Pet.objects.get(id=_to_object_id(pet_id))


def _validate_weight_log(pet, data):
    weight = data.get("weight")
    if weight is None:
        raise ValueError("Weight is required.")
    try:
        data["weight"] = float(weight)
    except (TypeError, ValueError):
        raise ValueError("Weight must be numeric.")
    if data["weight"] <= 0:
        raise ValueError("Weight must be greater than zero.")

    logged_at = data.get("logged_at")
    if logged_at is None:
        raise ValueError("Logged date is required.")

    logged_day = _date_part(logged_at)
    birth_day = _date_part(getattr(pet, "birth_date", None))
    if logged_day is not None and birth_day is not None and logged_day < birth_day:
        raise ValueError(f"Weight log date cannot be before pet birth date ({birth_day.isoformat()}).")


def list_weight_logs(user, pet_id):
    _get_owned_pet(user, pet_id)
    return WeightLog.objects.filter(pet_id=_to_object_id(pet_id)).order_by("-logged_at")


def create_weight_log(user, pet_id, data):
    data = parse_payload_dates(translate_payload(data))
    pet = _get_owned_pet(user, pet_id)
    data["pet_id"] = pet.id
    data["owner_id"] = user.id
    _validate_weight_log(pet, data)

    client_mutation_id = data.get("client_mutation_id")
    if client_mutation_id:
        existing = WeightLog.objects.filter(
            owner_id=user.id,
            client_mutation_id=client_mutation_id,
        ).first()
        if existing:
            return existing

    created = WeightLog.objects.create(**data)
    return WeightLog.objects.get(id=created.id)


def get_weight_log(user, pet_id, weight_log_id):
    _get_owned_pet(user, pet_id)
    return WeightLog.objects.get(id=_to_object_id(weight_log_id), pet_id=_to_object_id(pet_id))


def update_weight_log(user, pet_id, weight_log_id, data):
    data = parse_payload_dates(translate_payload(data))
    pet = _get_owned_pet(user, pet_id)
    weight_log = WeightLog.objects.get(id=_to_object_id(weight_log_id), pet_id=pet.id)

    merged = {
        "weight": data.get("weight", weight_log.weight),
        "logged_at": data.get("logged_at", weight_log.logged_at),
    }
    _validate_weight_log(pet, merged)

    if "weight" in data:
        weight_log.weight = merged["weight"]
    if "logged_at" in data:
        weight_log.logged_at = merged["logged_at"]
    weight_log.save()
    return WeightLog.objects.get(id=weight_log.id)


def delete_weight_log(user, pet_id, weight_log_id):
    _get_owned_pet(user, pet_id)
    WeightLog.objects.filter(id=_to_object_id(weight_log_id), pet_id=_to_object_id(pet_id)).delete()
