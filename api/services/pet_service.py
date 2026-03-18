# CRUD logic for Pet
from api.models import Pet, Vaccination, AttachedDocument
from bson import ObjectId
from datetime import datetime, date

# Mapping of camelCase API payload keys → snake_case model field names
_CAMEL_TO_SNAKE = {
    # Pet fields
    "birthDate": "birth_date",
    "photoUrl": "photo_url",
    "isNfcSynced": "is_nfc_synced",
    "knownAllergies": "known_allergies",
    "defaultVet": "default_vet",
    "defaultClinic": "default_clinic",
    # Vaccination embedded fields
    "vaccineId": "vaccine_id",
    "dateGiven": "date_given",
    "nextDueDate": "next_due_date",
    "lotNumber": "lot_number",
    "administeredBy": "administered_by",
    "clinicName": "clinic_name",
    "attachedDocuments": "attached_documents",
    # AttachedDocument embedded fields
    "documentId": "document_id",
    "fileName": "file_name",
    "fileUri": "file_uri",
}


def translate_payload(data):
    """Recursively translate camelCase API payload keys to snake_case model field names."""
    if isinstance(data, dict):
        translated = {_CAMEL_TO_SNAKE.get(k, k): translate_payload(v) for k, v in data.items()}
        return _convert_object_ids(translated)
    if isinstance(data, list):
        return [translate_payload(item) for item in data]
    return data


def _to_object_id(val):
    if val is None:
        return None
    if isinstance(val, ObjectId):
        return val
    if isinstance(val, str):
        try:
            return ObjectId(val)
        except Exception:
            return val
    return val


def _convert_object_ids(data):
    """Normalize known ObjectId fields inside an already-translated dict."""
    if not isinstance(data, dict):
        return data

    if "vaccine_id" in data:
        data["vaccine_id"] = _to_object_id(data["vaccine_id"])

    if "document_id" in data:
        data["document_id"] = _to_object_id(data["document_id"])

    if "owners" in data and isinstance(data["owners"], list):
        data["owners"] = [_to_object_id(oid) for oid in data["owners"]]

    if "attached_documents" in data and isinstance(data["attached_documents"], list):
        data["attached_documents"] = [
            _convert_object_ids(doc) if isinstance(doc, dict) else doc
            for doc in data["attached_documents"]
        ]

    if "vaccinations" in data and isinstance(data["vaccinations"], list):
        data["vaccinations"] = [
            _convert_object_ids(v) if isinstance(v, dict) else v
            for v in data["vaccinations"]
        ]

    return data


def _attached_document_to_dict(doc):
    if isinstance(doc, dict):
        normalized = dict(doc)
        if "document_id" in normalized:
            normalized["document_id"] = _to_object_id(normalized["document_id"])
        return normalized
    return {
        "document_id": getattr(doc, "document_id", None),
        "file_name": getattr(doc, "file_name", None),
        "file_uri": getattr(doc, "file_uri", None),
    }


def _vaccination_to_dict(v):
    if isinstance(v, dict):
        normalized = dict(v)
        if "vaccine_id" in normalized:
            normalized["vaccine_id"] = _to_object_id(normalized["vaccine_id"])
        if "date_given" in normalized:
            normalized["date_given"] = _to_datetime(normalized["date_given"])
        if "next_due_date" in normalized:
            normalized["next_due_date"] = _to_datetime(normalized["next_due_date"])
        if "attached_documents" in normalized and isinstance(normalized["attached_documents"], list):
            normalized["attached_documents"] = [
                _attached_document_to_dict(doc)
                for doc in normalized["attached_documents"]
            ]
        return normalized
    return {
        "vaccine_id": _to_object_id(getattr(v, "vaccine_id", None)),
        "date_given": _to_datetime(getattr(v, "date_given", None)),
        "next_due_date": _to_datetime(getattr(v, "next_due_date", None)),
        "lot_number": getattr(v, "lot_number", None),
        "status": getattr(v, "status", None),
        "administered_by": getattr(v, "administered_by", None),
        "clinic_name": getattr(v, "clinic_name", None),
        "attached_documents": [
            _attached_document_to_dict(doc)
            for doc in (getattr(v, "attached_documents", None) or [])
        ],
    }


def _normalize_vaccinations(vaccinations):
    return [_vaccination_to_dict(v) for v in (vaccinations or [])]


def _ids_equal(a, b):
    if a is None or b is None:
        return False
    return str(a) == str(b)


def _date_part(val):
    if val is None:
        return None
    dt = _to_datetime(val)
    if isinstance(dt, datetime):
        return dt.date()
    if isinstance(dt, date):
        return dt
    return None


def _dates_equal(a, b):
    da = _date_part(a)
    db = _date_part(b)
    if da is None or db is None:
        return False
    return da == db


def _to_datetime(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return val
    return val


def parse_payload_dates(data):
    """Convert date strings in the payload to Python datetime objects."""
    if isinstance(data, dict):
        if "birth_date" in data:
            data["birth_date"] = _to_datetime(data["birth_date"])

        if "vaccinations" in data and isinstance(data["vaccinations"], list):
            for v in data["vaccinations"]:
                if isinstance(v, dict):
                    if "date_given" in v:
                        v["date_given"] = _to_datetime(v["date_given"])
                    if "next_due_date" in v:
                        v["next_due_date"] = _to_datetime(v["next_due_date"])

        if "date_given" in data:
            data["date_given"] = _to_datetime(data["date_given"])
        if "next_due_date" in data:
            data["next_due_date"] = _to_datetime(data["next_due_date"])
    return data


def create_pet(user, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    
    if not data.get("owners"):
        data["owners"] = [user.id]
    elif user.id not in data["owners"]:
        data["owners"].append(user.id)
        
    pet = Pet.objects.create(**data)
    
    # Associate pet with user
    if pet.id not in user.pets:
        user.pets.append(pet.id)
        user.save()
        
    return Pet.objects.get(id=pet.id)


def list_pets():
    return Pet.objects.all()


def list_pets_by_owner(owner_id):
    return Pet.objects.filter(owners__contains=[owner_id])


def get_pet(pet_id):
    return Pet.objects.get(id=pet_id)


def update_pet(pet_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)

    update_fields = {}

    for key, value in data.items():
        update_fields[key] = value

    Pet.objects.filter(id=pet_id).update(**update_fields)

    return Pet.objects.get(id=pet_id)


def delete_pet(pet_id):
    Pet.objects.filter(id=pet_id).delete()


def add_vaccination(pet_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    pet = Pet.objects.get(id=pet_id)

    pet.vaccinations = _normalize_vaccinations(pet.vaccinations)
    pet.vaccinations.append(data)
    pet.save()
    return Pet.objects.get(id=pet.id)


def add_document_to_vaccination(pet_id, vaccination_id, document_data):
    document_data = translate_payload(document_data)
    pet = Pet.objects.get(id=pet_id)
    target_id = _to_object_id(vaccination_id)
    if pet.vaccinations:
        normalized = []
        for vaccination in pet.vaccinations:
            v = _vaccination_to_dict(vaccination)
            if _ids_equal(v.get("vaccine_id"), target_id):
                docs = v.get("attached_documents") or []
                docs.append(document_data)
                v["attached_documents"] = docs
            normalized.append(v)
        pet.vaccinations = normalized
    pet.save()
    return Pet.objects.get(id=pet.id)


def update_vaccination(pet_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)

    if "vaccine_id" not in data or "date_given" not in data:
        raise Exception("vaccineId and dateGiven are required to identify the vaccination")

    target_id = _to_object_id(data["vaccine_id"])
    target_date = data["date_given"]

    pet = Pet.objects.get(id=pet_id)

    updated = False
    normalized = []
    for vaccination in (pet.vaccinations or []):
        v = _vaccination_to_dict(vaccination)
        if _ids_equal(v.get("vaccine_id"), target_id) and _dates_equal(v.get("date_given"), target_date):
            for key, value in data.items():
                if key in ("vaccine_id", "date_given"):
                    continue
                v[key] = value
            updated = True
        normalized.append(v)

    if not updated:
        raise Exception("Vaccination not found for the given vaccineId and dateGiven")

    pet.vaccinations = normalized
    pet.save()
    return Pet.objects.get(id=pet.id)


def delete_vaccination(pet_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)

    if "vaccine_id" not in data or "date_given" not in data:
        raise Exception("vaccineId and dateGiven are required to identify the vaccination")

    target_id = _to_object_id(data["vaccine_id"])
    target_date = data["date_given"]

    pet = Pet.objects.get(id=pet_id)

    deleted = False
    normalized = []
    for vaccination in (pet.vaccinations or []):
        v = _vaccination_to_dict(vaccination)
        if _ids_equal(v.get("vaccine_id"), target_id) and _dates_equal(v.get("date_given"), target_date):
            deleted = True
            continue
        normalized.append(v)

    if not deleted:
        raise Exception("Vaccination not found for the given vaccineId and dateGiven")

    pet.vaccinations = normalized
    pet.save()
    return Pet.objects.get(id=pet.id)
