# CRUD logic for Pet
from api.models import Pet, Vaccination, AttachedDocument
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
        return {_CAMEL_TO_SNAKE.get(k, k): translate_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [translate_payload(item) for item in data]
    return data


def _to_datetime(val):
    if not val:
        return None
    if isinstance(val, (datetime, date)):
        return val
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

    if pet.vaccinations is None:
        pet.vaccinations = []

    pet.vaccinations.append(data)
    pet.save()
    return Pet.objects.get(id=pet.id)


def add_document_to_vaccination(pet_id, vaccination_id, document_data):
    document_data = translate_payload(document_data)
    pet = Pet.objects.get(id=pet_id)
    if pet.vaccinations:
        for vaccination in pet.vaccinations:
            if vaccination.vaccine_id == vaccination_id:
                if vaccination.attached_documents is None:
                    vaccination.attached_documents = []
                vaccination.attached_documents.append(document_data)
                break
    pet.save()
    return Pet.objects.get(id=pet.id)