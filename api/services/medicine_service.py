from datetime import date, datetime

from api.models.medicine import Medicine
from api.models.pet import Pet
from api.serializers.pet_serializer import _to_object_id


_CAMEL_TO_SNAKE = {
    "petId": "pet_id",
    "ownerId": "owner_id",
    "medicineName": "medicine_name",
    "administrationRoute": "administration_route",
    "dosageValue": "dosage_value",
    "dosageUnit": "dosage_unit",
    "startDate": "start_date",
    "endDate": "end_date",
    "photoUrl": "photo_url",
    "reminderEnabled": "reminder_enabled",
    "lastAdministered": "last_administered",
}

_DATETIME_FALLBACK_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
]


def translate_payload(data):
    if isinstance(data, dict):
        return {_CAMEL_TO_SNAKE.get(key, key): translate_payload(value) for key, value in data.items()}
    if isinstance(data, list):
        return [translate_payload(item) for item in data]
    return data


def parse_payload_dates(data):
    date_fields = {"start_date", "end_date", "last_administered"}
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
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
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


def _ensure_pet_belongs_to_user(user, pet_id):
    if not pet_id:
        raise ValueError("pet_id is required")

    pet = Pet.objects.get(id=_to_object_id(pet_id))
    user_pet_ids = [str(pid) for pid in (user.pets or [])]
    if str(pet.id) not in user_pet_ids:
        raise PermissionError("Not authorized to access this pet's medicines")


def create_medicine(user, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    # Expect pet_id to be provided in payload
    pet_id = data.get("pet_id")
    if not pet_id:
        raise ValueError("petId is required in payload")
    _ensure_pet_belongs_to_user(user, pet_id)
    data["owner_id"] = user.id
    data["pet_id"] = _to_object_id(pet_id)
    medicine = Medicine.objects.create(**data)
    return Medicine.objects.get(id=medicine.id)


def list_medicines_for_pet(pet_id):
    if not pet_id:
        return Medicine.objects.none()
    return Medicine.objects.filter(pet_id=_to_object_id(pet_id))


def list_medicines(filters=None):
    if filters:
        return Medicine.objects.filter(**filters)
    return Medicine.objects.all()


def get_medicine(medicine_id):
    return Medicine.objects.get(id=_to_object_id(medicine_id))


def update_medicine(medicine_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    medicine = Medicine.objects.get(id=_to_object_id(medicine_id))
    for key in ["owner_id", "pet_id"]:
        data.pop(key, None)
    for key, value in data.items():
        setattr(medicine, key, value)
    medicine.save()
    return Medicine.objects.get(id=medicine.id)


def delete_medicine(medicine_id):
    Medicine.objects.filter(id=_to_object_id(medicine_id)).delete()