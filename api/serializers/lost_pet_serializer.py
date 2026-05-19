from datetime import timezone


def format_datetime(value):
    if not value:
        return None
    if hasattr(value, "isoformat"):
        if getattr(value, "tzinfo", None) is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def _value(source, attr, default=None):
    if isinstance(source, dict):
        return source.get(attr, default)
    return getattr(source, attr, default)


def emergency_contact_to_dict(contact, public=False):
    phone = _value(contact, "phone", "")
    whatsapp = _value(contact, "whatsapp", "")
    expose_phone = bool(_value(contact, "expose_phone", False))
    expose_whatsapp = bool(_value(contact, "expose_whatsapp", False))

    data = {
        "name": _value(contact, "name", ""),
        "relationship": _value(contact, "relationship", ""),
        "preferred": bool(_value(contact, "preferred", False)),
    }

    if public:
        data["phone"] = phone if expose_phone else ""
        data["whatsapp"] = whatsapp if expose_whatsapp else ""
        return data

    data.update({
        "phone": phone,
        "whatsapp": whatsapp,
        "exposePhone": expose_phone,
        "exposeWhatsapp": expose_whatsapp,
    })
    return data


def lost_pet_report_card_to_dict(report, pet):
    """Serialize an active report for public listing with owner-approved contacts."""
    return {
        "id": str(report.id),
        "pet": {
            "id": str(pet.id),
            "name": pet.name,
            "species": pet.species,
            "breed": pet.breed,
            "color": pet.color,
            "photoUrl": pet.photo_url,
            "status": pet.status,
        },
        "lastSeenLocation": report.last_seen_location,
        "lastSeenLatitude": report.last_seen_latitude,
        "lastSeenLongitude": report.last_seen_longitude,
        "lastSeenAt": format_datetime(report.last_seen_at),
        "emergencyContacts": [
            contact for contact in (
                emergency_contact_to_dict(c, public=True)
                for c in (report.emergency_contacts or [])
            )
            if contact.get("phone") or contact.get("whatsapp")
        ],
        "createdAt": format_datetime(report.created_at),
        "updatedAt": format_datetime(report.updated_at),
    }


def lost_pet_report_detail_to_dict(report, pet):
    """Serialize a public report detail with only owner-approved contact data."""
    data = lost_pet_report_card_to_dict(report, pet)
    data.update({
        "lostNote": report.lost_note,
        "knownAllergies": pet.known_allergies if getattr(report, "expose_medical_info", False) else "",
        "exposeMedicalInfo": bool(getattr(report, "expose_medical_info", False)),
        "emergencyContacts": [
            contact for contact in (
                emergency_contact_to_dict(c, public=True)
                for c in (report.emergency_contacts or [])
            )
            if contact.get("phone") or contact.get("whatsapp")
        ],
    })
    return data


def lost_pet_report_owner_to_dict(report, pet=None):
    data = {
        "id": str(report.id),
        "schema": getattr(report, "schema", 1),
        "petId": str(report.pet_id),
        "ownerId": str(report.owner_id),
        "status": report.status,
        "lostNote": report.lost_note,
        "lastSeenLocation": report.last_seen_location,
        "lastSeenLatitude": report.last_seen_latitude,
        "lastSeenLongitude": report.last_seen_longitude,
        "lastSeenAt": format_datetime(report.last_seen_at),
        "exposeMedicalInfo": bool(getattr(report, "expose_medical_info", False)),
        "nfcNotificationsEnabled": getattr(
            report,
            "nfc_notifications_enabled",
            True,
        )
        is not False,
        "knownAllergies": getattr(pet, "known_allergies", "") if getattr(report, "expose_medical_info", False) else "",
        "emergencyContacts": [
            emergency_contact_to_dict(c)
            for c in (report.emergency_contacts or [])
        ],
        "createdAt": format_datetime(report.created_at),
        "updatedAt": format_datetime(report.updated_at),
        "resolvedAt": format_datetime(report.resolved_at),
    }
    if pet is not None:
        data["petStatus"] = pet.status
        data["pet"] = {
            "id": str(pet.id),
            "name": pet.name,
            "species": pet.species,
            "breed": pet.breed,
            "color": pet.color,
            "photoUrl": pet.photo_url,
            "status": pet.status,
        }
    return data


def lost_pet_sighting_to_dict(sighting):
    return {
        "id": str(sighting.id),
        "schema": getattr(sighting, "schema", 1),
        "reportId": str(sighting.report_id),
        "petId": str(sighting.pet_id),
        "seenAt": format_datetime(sighting.seen_at),
        "location": sighting.location,
        "latitude": sighting.latitude,
        "longitude": sighting.longitude,
        "note": sighting.note,
        "photoUrl": sighting.photo_url,
        "reporterName": sighting.reporter_name,
        "reporterPhone": sighting.reporter_phone,
        "reporterEmail": sighting.reporter_email,
        "createdAt": format_datetime(sighting.created_at),
    }
