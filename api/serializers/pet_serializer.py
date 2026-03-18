from datetime import date, datetime

from bson import ObjectId


def format_date(d):
    if d is None:
        return None
    if isinstance(d, (date, datetime)):
        return d.isoformat().replace('+00:00', 'Z')
    return d


def pet_to_dict(pet):
    """Serialize Pet model to dictionary."""
    if not pet:
        return None

    def format_date(d):
        if not d:
            return None
        return d.isoformat() if hasattr(d, "isoformat") else str(d)

    return {
        "id": str(pet.id),
        "schema": getattr(pet, "schema", 1),
        "owners": [str(oid) for oid in (pet.owners or [])],
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "gender": pet.gender,
        "birthDate": format_date(pet.birth_date),
        "weight": float(pet.weight) if pet.weight is not None else None,
        "color": pet.color,
        "photoUrl": pet.photo_url,
        "status": pet.status,
        "isNfcSynced": pet.is_nfc_synced,
        "knownAllergies": pet.known_allergies,
        "defaultVet": pet.default_vet,
        "defaultClinic": pet.default_clinic,
        "vaccinations": [vaccination_to_api_dict(v) for v in (pet.vaccinations or [])],
    }


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


def vaccination_to_dict(v):
    if isinstance(v, dict):
        normalized = dict(v)
        if "_id" not in normalized and "id" in normalized:
            normalized["_id"] = normalized["id"]
        if "_id" in normalized:
            normalized["_id"] = _to_object_id(normalized["_id"])
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
        "_id": _to_object_id(getattr(v, "id", None)),
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


def vaccination_to_api_dict(v):
    v_dict = vaccination_to_dict(v)
    return {
        "id": str(v_dict["_id"]) if v_dict.get("_id") is not None else None,
        "vaccineId": str(v_dict["vaccine_id"]) if v_dict.get("vaccine_id") is not None else None,
        "dateGiven": format_date(v_dict.get("date_given")),
        "nextDueDate": format_date(v_dict.get("next_due_date")),
        "lotNumber": v_dict.get("lot_number"),
        "status": v_dict.get("status"),
        "administeredBy": v_dict.get("administered_by"),
        "clinicName": v_dict.get("clinic_name"),
        "attachedDocuments": [
            {
                "documentId": str(doc.get("document_id")) if doc.get("document_id") is not None else None,
                "fileName": doc.get("file_name"),
                "fileUri": doc.get("file_uri"),
            }
            for doc in (v_dict.get("attached_documents") or [])
        ],
    }
