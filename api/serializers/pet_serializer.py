from datetime import date, datetime


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
        "vaccinations": [
            {
                "vaccineId": str(v.vaccine_id),
                "dateGiven": format_date(v.date_given),
                "nextDueDate": format_date(v.next_due_date),
                "lotNumber": v.lot_number,
                "status": v.status,
                "administeredBy": v.administered_by,
                "clinicName": v.clinic_name,
                "attachedDocuments": [
                    {
                        "documentId": str(doc.document_id),
                        "fileName": doc.file_name,
                        "fileUri": doc.file_uri,
                    }
                    for doc in (v.attached_documents or [])
                ],
            }
            for v in (pet.vaccinations or [])
        ],
    }