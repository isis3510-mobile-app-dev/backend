# CRUD logic for Pet
from api.models import Pet, Vaccination, AttachedDocument
from api.serializers.pet_serializer import vaccination_to_dict, _to_object_id, _to_datetime
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

def _normalize_vaccinations(vaccinations):
    return [vaccination_to_dict(v) for v in (vaccinations or [])]


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

def list_vaccinations(pet_id):
    pet = Pet.objects.get(id=pet_id)
    return pet.vaccinations or []

def add_vaccination(pet_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)
    pet = Pet.objects.get(id=pet_id)

    pet.vaccinations = _normalize_vaccinations(pet.vaccinations)
    if "_id" not in data and "id" in data:
        data["_id"] = _to_object_id(data["id"])
    if "_id" not in data:
        data["_id"] = _to_object_id(ObjectId())
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
            v = vaccination_to_dict(vaccination)
            if _ids_equal(v.get("_id"), target_id):
                docs = v.get("attached_documents") or []
                docs.append(document_data)
                v["attached_documents"] = docs
            normalized.append(v)
        pet.vaccinations = normalized
    pet.save()
    return Pet.objects.get(id=pet.id)


def update_vaccination(pet_id, vaccination_id, data):
    data = translate_payload(data)
    data = parse_payload_dates(data)

    target_id = _to_object_id(vaccination_id)
    pet = Pet.objects.get(id=pet_id)

    updated = False
    normalized = []
    for vaccination in (pet.vaccinations or []):
        v = vaccination_to_dict(vaccination)
        if _ids_equal(v.get("_id"), target_id):
            for key, value in data.items():
                if key in ("_id", "id"):
                    continue
                v[key] = value
            updated = True
        normalized.append(v)

    if not updated:
        raise Exception("Vaccination not found for the given id")

    pet.vaccinations = normalized
    pet.save()
    return Pet.objects.get(id=pet.id)


def update_vaccination_date(pet_id, vaccine_id, old_date, new_date):
    """Update a vaccination, allowing dateGiven to be changed."""
    vaccine_id = _to_object_id(vaccine_id)
    old_date = _to_datetime(old_date)
    new_date = _to_datetime(new_date)

    pet = Pet.objects.get(id=pet_id)

    updated = False
    normalized = []
    for vaccination in (pet.vaccinations or []):
        v = _vaccination_to_dict(vaccination)
        if _ids_equal(v.get("vaccine_id"), vaccine_id) and _dates_equal(v.get("date_given"), old_date):
            v["date_given"] = new_date
            updated = True
        normalized.append(v)

    if not updated:
        raise Exception("Vaccination not found for the given vaccineId and dateGiven")

    pet.vaccinations = normalized
    pet.save()
    return Pet.objects.get(id=pet.id)

def delete_vaccination(pet_id, vaccination_id):
    target_id = _to_object_id(vaccination_id)

    pet = Pet.objects.get(id=pet_id)

    deleted = False
    normalized = []
    for vaccination in (pet.vaccinations or []):
        v = vaccination_to_dict(vaccination)
        if _ids_equal(v.get("_id"), target_id):
            deleted = True
            continue
        normalized.append(v)

    if not deleted:
        raise Exception("Vaccination not found for the given id")

    pet.vaccinations = normalized
    pet.save()
    return Pet.objects.get(id=pet.id)
