from datetime import timezone


def format_date(value):
    if not value:
        return None
    if hasattr(value, "isoformat"):
        if getattr(value, "tzinfo", None) is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def medicine_to_dict(medicine):
    if not medicine:
        return None

    return {
        "medicineId": str(medicine.id),
        "schema": getattr(medicine, "schema", 1),
        "petId": str(medicine.pet_id),
        "ownerId": str(medicine.owner_id),
        "medicineName": medicine.medicine_name,
        "administrationRoute": medicine.administration_route,
        "dosageValue": float(medicine.dosage_value) if medicine.dosage_value is not None else None,
        "dosageUnit": medicine.dosage_unit,
        "frequency": medicine.frequency,
        "startDate": format_date(medicine.start_date),
        "endDate": format_date(medicine.end_date),
        "photoUrl": medicine.photo_url,
        "reminderEnabled": medicine.reminder_enabled,
        "lastAdministered": format_date(medicine.last_administered),
    }