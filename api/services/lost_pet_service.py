import random
from datetime import datetime, timezone as dt_timezone

from django.utils import timezone

from api.models import LostPetReport, LostPetSighting, Pet, User
from api.serializers.pet_serializer import _to_object_id


_CAMEL_TO_SNAKE = {
    "petId": "pet_id",
    "ownerId": "owner_id",
    "reportId": "report_id",
    "lostNote": "lost_note",
    "lastSeenLocation": "last_seen_location",
    "lastSeenLatitude": "last_seen_latitude",
    "lastSeenLongitude": "last_seen_longitude",
    "lastSeenAt": "last_seen_at",
    "emergencyContacts": "emergency_contacts",
    "exposePhone": "expose_phone",
    "exposeWhatsapp": "expose_whatsapp",
    "exposeMedicalInfo": "expose_medical_info",
    "nfcNotificationsEnabled": "nfc_notifications_enabled",
    "seenAt": "seen_at",
    "photoUrl": "photo_url",
    "reporterName": "reporter_name",
    "reporterPhone": "reporter_phone",
    "reporterEmail": "reporter_email",
}

_REPORT_FIELDS = {
    "lost_note",
    "last_seen_location",
    "last_seen_latitude",
    "last_seen_longitude",
    "last_seen_at",
    "emergency_contacts",
    "expose_medical_info",
    "nfc_notifications_enabled",
}

_SIGHTING_FIELDS = {
    "seen_at",
    "location",
    "latitude",
    "longitude",
    "note",
    "photo_url",
    "reporter_name",
    "reporter_phone",
    "reporter_email",
}

_DATETIME_FALLBACK_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
]

_NORTH_BOGOTA_POINTS = [
    ("Usaquén, Bogotá", 4.7038, -74.0309),
    ("Chicó Norte, Bogotá", 4.6787, -74.0488),
    ("Santa Bárbara, Bogotá", 4.6995, -74.0443),
    ("Cedritos, Bogotá", 4.7284, -74.0448),
    ("Parque El Virrey, Bogotá", 4.6741, -74.0539),
    ("Colina Campestre, Bogotá", 4.7416, -74.0661),
    ("Country Club, Bogotá", 4.7244, -74.0511),
    ("La Castellana, Bogotá", 4.6868, -74.0648),
]


def translate_payload(data):
    if isinstance(data, dict):
        return {_CAMEL_TO_SNAKE.get(k, k): translate_payload(v) for k, v in data.items()}
    if isinstance(data, list):
        return [translate_payload(item) for item in data]
    return data


def parse_payload_dates(data):
    date_fields = {"last_seen_at", "seen_at"}
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


def _parse_datetime_value(field_name, raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None

    try:
        return _ensure_aware_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        pass

    for fmt in _DATETIME_FALLBACK_FORMATS:
        try:
            return _ensure_aware_datetime(datetime.strptime(value, fmt))
        except ValueError:
            continue

    raise ValueError(f"Invalid {field_name} format. Expected ISO datetime or YYYY-MM-DD / DD/MM/YYYY.")


def _ensure_aware_datetime(value):
    if value is None or not isinstance(value, datetime):
        return value
    if timezone.is_naive(value):
        return timezone.make_aware(value, dt_timezone.utc)
    return value


def _prepare_payload(data):
    data = translate_payload(data or {})
    data = parse_payload_dates(data)
    return data


def _clean_contacts(contacts):
    cleaned = []
    for contact in contacts or []:
        cleaned_contact = _contact_to_dict(contact)
        if cleaned_contact:
            cleaned.append(cleaned_contact)
    return cleaned


def _contact_to_dict(contact):
    if contact is None:
        return None

    def value(key, default=""):
        if isinstance(contact, dict):
            return contact.get(key, default)
        return getattr(contact, key, default)

    return {
        "name": value("name", ""),
        "phone": value("phone", ""),
        "whatsapp": value("whatsapp", ""),
        "relationship": value("relationship", ""),
        "expose_phone": bool(value("expose_phone", False)),
        "expose_whatsapp": bool(value("expose_whatsapp", False)),
        "preferred": bool(value("preferred", False)),
    }


def _normalize_report_contacts(report):
    report.emergency_contacts = _clean_contacts(report.emergency_contacts)
    return report


def _report_payload(data):
    payload = {
        key: value
        for key, value in _prepare_payload(data).items()
        if key in _REPORT_FIELDS
    }
    if "emergency_contacts" in payload:
        payload["emergency_contacts"] = _clean_contacts(payload["emergency_contacts"])
    return payload


def _sighting_payload(data):
    return {
        key: value
        for key, value in _prepare_payload(data).items()
        if key in _SIGHTING_FIELDS
    }


def _reports_for_pet(pet_id):
    return LostPetReport.objects.filter(pet_id=_to_object_id(pet_id))


def _newest_report_for_pet(pet_id):
    reports = list(_reports_for_pet(pet_id))
    if not reports:
        return None
    return sorted(
        reports,
        key=lambda report: report.created_at or datetime.min.replace(tzinfo=dt_timezone.utc),
        reverse=True,
    )[0]


def _newest_active_report_for_pet(pet_id):
    reports = [
        report for report in list(_reports_for_pet(pet_id))
        if report.status == "active"
    ]
    if not reports:
        return None
    return sorted(
        reports,
        key=lambda report: report.created_at or datetime.min.replace(tzinfo=dt_timezone.utc),
        reverse=True,
    )[0]


def _set_pet_status(pet_id, status):
    Pet.objects.filter(id=_to_object_id(pet_id)).update(status=status)


def _resolve_active_reports_for_pet(pet_id):
    resolved_at = timezone.now()
    for report in [
        item for item in list(_reports_for_pet(pet_id))
        if item.status != "resolved"
    ]:
        report.status = "resolved"
        report.resolved_at = resolved_at
        _normalize_report_contacts(report)
        report.save()


def list_active_reports():
    return LostPetReport.objects.filter(status="active")


def list_active_reports_with_pets():
    latest_by_pet = {}
    for report in sorted(
        list(list_active_reports()),
        key=lambda item: item.updated_at or item.created_at or datetime.min.replace(tzinfo=dt_timezone.utc),
        reverse=True,
    ):
        latest_by_pet.setdefault(str(report.pet_id), report)

    results = []
    for report in latest_by_pet.values():
        try:
            pet = _get_pet_for_lost_report(report.pet_id)
        except Exception:
            continue
        if pet.status != "lost":
            continue
        results.append((report, pet))
    return results


def get_public_report(report_id):
    report = LostPetReport.objects.get(id=_to_object_id(report_id), status="active")
    pet = _get_pet_for_lost_report(report.pet_id, include_medical=True)
    if pet.status != "lost":
        raise ValueError("Lost pet report not found")
    return report, pet


def get_report_for_pet(pet_id):
    report = _newest_report_for_pet(pet_id)
    if not report:
        raise LostPetReport.DoesNotExist("Lost pet report not found")
    pet = Pet.objects.get(id=_to_object_id(pet_id))
    return report, pet


def create_or_reactivate_report(pet_id, owner_id, data):
    pet = Pet.objects.get(id=_to_object_id(pet_id))
    payload = _report_payload(data)
    should_start_new_episode = pet.status != "lost"
    report = None if should_start_new_episode else _newest_active_report_for_pet(pet_id)

    if report:
        for key, value in payload.items():
            setattr(report, key, value)
        report.status = "active"
        report.owner_id = _to_object_id(owner_id)
        report.resolved_at = None
        _normalize_report_contacts(report)
        report.save()
    else:
        _resolve_active_reports_for_pet(pet_id)
        report = LostPetReport.objects.create(
            pet_id=_to_object_id(pet_id),
            owner_id=_to_object_id(owner_id),
            status="active",
            **payload,
        )
        report = LostPetReport.objects.get(id=report.id)

    _set_pet_status(pet_id, "lost")
    return report, Pet.objects.get(id=pet.id)


def update_report_for_pet(pet_id, data):
    report = _newest_report_for_pet(pet_id)
    if not report:
        raise LostPetReport.DoesNotExist("Lost pet report not found")
    if report.status != "active":
        return create_or_reactivate_report(pet_id, report.owner_id, data)

    for key, value in _report_payload(data).items():
        setattr(report, key, value)
    report.status = "active"
    report.resolved_at = None
    _normalize_report_contacts(report)
    report.save()
    _set_pet_status(pet_id, "lost")
    pet = Pet.objects.get(id=_to_object_id(pet_id))
    return LostPetReport.objects.get(id=report.id), pet


def mark_pet_found(pet_id):
    pet = Pet.objects.get(id=_to_object_id(pet_id))
    reports = list(_reports_for_pet(pet_id))
    report = sorted(
        reports,
        key=lambda item: item.updated_at or item.created_at or datetime.min.replace(tzinfo=dt_timezone.utc),
        reverse=True,
    )[0] if reports else None
    _resolve_active_reports_for_pet(pet_id)

    if report and report.status != "resolved":
        report.status = "resolved"
        report.resolved_at = report.resolved_at or timezone.now()
        _normalize_report_contacts(report)
    _set_pet_status(pet_id, "healthy")
    return report, Pet.objects.get(id=pet.id)


def backfill_lost_reports_for_lost_pets(commit=False, limit=None):
    """Create active lost reports for historical pets already marked as lost."""
    pets = list(_pet_lost_queryset())
    if limit is not None:
        pets = pets[:limit]

    results = []
    for pet in pets:
        existing_report = _newest_report_for_pet(pet.id)
        if existing_report and existing_report.status == "active":
            results.append({
                "pet_id": str(pet.id),
                "pet_name": pet.name,
                "action": "skipped_active_report_exists",
                "report_id": str(existing_report.id),
            })
            continue

        owner = _owner_for_pet(pet)
        if owner is None:
            results.append({
                "pet_id": str(pet.id),
                "pet_name": pet.name,
                "action": "skipped_missing_owner",
                "report_id": None,
            })
            continue

        location_name, latitude, longitude = _north_bogota_point_for_pet(pet.id)
        report_data = {
            "owner_id": owner.id,
            "status": "active",
            "lost_note": "",
            "last_seen_location": location_name,
            "last_seen_latitude": latitude,
            "last_seen_longitude": longitude,
            "last_seen_at": timezone.now(),
            "expose_medical_info": False,
            "nfc_notifications_enabled": True,
            "emergency_contacts": [_owner_contact_to_dict(owner)],
            "resolved_at": None,
        }

        if commit:
            if existing_report:
                for key, value in report_data.items():
                    setattr(existing_report, key, value)
                existing_report.save()
                report = LostPetReport.objects.get(id=existing_report.id)
                action = "reactivated_report"
            else:
                report = LostPetReport.objects.create(
                    pet_id=_to_object_id(pet.id),
                    **report_data,
                )
                report = LostPetReport.objects.get(id=report.id)
                action = "created_report"
        else:
            report = existing_report
            action = "would_reactivate_report" if existing_report else "would_create_report"

        results.append({
            "pet_id": str(pet.id),
            "pet_name": pet.name,
            "action": action,
            "report_id": str(report.id) if report else None,
            "owner_id": str(owner.id),
            "last_seen_location": location_name,
        })

    return results


def _pet_lost_queryset():
    return Pet.objects.filter(status="lost").only(
        "id",
        "name",
        "owners",
        "status",
    )


def _get_pet_for_lost_report(pet_id, include_medical=False):
    fields = [
        "id",
        "name",
        "species",
        "breed",
        "color",
        "photo_url",
        "status",
    ]
    if include_medical:
        fields.extend(["known_allergies", "default_vet", "default_clinic"])
    return Pet.objects.only(*fields).get(id=_to_object_id(pet_id))


def _owner_for_pet(pet):
    owners = list(pet.owners or [])
    for owner_id in owners:
        try:
            return User.objects.get(id=_to_object_id(owner_id))
        except Exception:
            continue

    try:
        users = list(User.objects.filter(pets__contains=[_to_object_id(pet.id)]))
    except Exception:
        users = []
    return users[0] if users else None


def _owner_contact_to_dict(owner):
    phone = (owner.phone or "").strip()
    return {
        "name": (owner.name or "Owner").strip() or "Owner",
        "phone": phone,
        "whatsapp": phone,
        "relationship": "Owner",
        "preferred": True,
        "expose_phone": False,
        "expose_whatsapp": False,
    }


def _north_bogota_point_for_pet(pet_id):
    rng = random.Random(str(pet_id))
    return rng.choice(_NORTH_BOGOTA_POINTS)


def create_sighting(report_id, data):
    report, pet = get_public_report(report_id)
    payload = _sighting_payload(data)
    _apply_location_label(payload)
    _validate_sighting_payload(payload)
    sighting = LostPetSighting.objects.create(
        report_id=_to_object_id(report.id),
        pet_id=_to_object_id(pet.id),
        **payload,
    )
    sighting = LostPetSighting.objects.get(id=sighting.id)

    if "location" in payload:
        report.last_seen_location = payload.get("location") or report.last_seen_location
    if "latitude" in payload:
        report.last_seen_latitude = payload.get("latitude")
    if "longitude" in payload:
        report.last_seen_longitude = payload.get("longitude")
    if "seen_at" in payload:
        report.last_seen_at = payload.get("seen_at") or report.last_seen_at
    _normalize_report_contacts(report)
    report.save()

    _notify_owner_of_sighting(report, pet, sighting)
    return sighting, LostPetReport.objects.get(id=report.id), pet


def _apply_location_label(payload):
    current = (payload.get("location") or "").strip()
    if current and current.lower() != "nfc scan location":
        return

    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if latitude is None or longitude is None:
        return

    try:
        payload["location"] = _nearest_bogota_zone(float(latitude), float(longitude))
    except (TypeError, ValueError):
        return


def _nearest_bogota_zone(latitude, longitude):
    name, _, _ = min(
        _NORTH_BOGOTA_POINTS,
        key=lambda point: ((point[1] - latitude) ** 2) + ((point[2] - longitude) ** 2),
    )
    return f"Near {name}"


def create_nfc_scan_sighting(pet_id, data):
    report = _active_report_for_pet(pet_id)
    if not report:
        raise LostPetReport.DoesNotExist("Active lost pet report not found")
    return create_sighting(report.id, data)


def _active_report_for_pet(pet_id):
    active_reports = list(
        LostPetReport.objects.filter(pet_id=_to_object_id(pet_id), status="active")
    )
    if not active_reports:
        return None
    return sorted(
        active_reports,
        key=lambda report: report.updated_at or report.created_at or datetime.min.replace(tzinfo=dt_timezone.utc),
        reverse=True,
    )[0]


def _validate_sighting_payload(payload):
    has_location_text = bool((payload.get("location") or "").strip())
    has_coordinates = payload.get("latitude") is not None and payload.get("longitude") is not None
    if not has_location_text and not has_coordinates:
        raise ValueError("A sighting needs a location or coordinates.")

    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if latitude is not None and not (-90 <= float(latitude) <= 90):
        raise ValueError("Invalid latitude.")
    if longitude is not None and not (-180 <= float(longitude) <= 180):
        raise ValueError("Invalid longitude.")


def _notify_owner_of_sighting(report, pet, sighting):
    if getattr(report, "nfc_notifications_enabled", True) is False:
        return

    try:
        from api.services import notification_service

        if not hasattr(notification_service, "create_notification"):
            return

        location = sighting.location or report.last_seen_location or "an unknown location"
        reporter_phone = (sighting.reporter_phone or "").strip()
        reporter_label = (sighting.reporter_name or "Someone").strip()
        contact_hint = f" Contact: {reporter_phone}." if reporter_phone else ""
        notification_service.create_notification({
            "userId": str(report.owner_id),
            "type": "lost_pet_sighting",
            "header": f"New sighting for {pet.name}",
            "text": f"{reporter_label} scanned {pet.name}'s NFC tag near {location}.{contact_hint}",
            "actionLabel": "Contact scanner" if reporter_phone else "",
            "actionPhone": reporter_phone,
            "actionWhatsapp": reporter_phone,
            "actionReportId": str(report.id),
            "actionPetId": str(pet.id),
            "actionPetName": (pet.name or "").strip(),
            "actionPetPhotoUrl": (pet.photo_url or "").strip(),
            "actionReporterName": reporter_label if reporter_label != "Someone" else "",
            "actionLocation": location,
            "actionLatitude": sighting.latitude,
            "actionLongitude": sighting.longitude,
        })
    except Exception:
        return
