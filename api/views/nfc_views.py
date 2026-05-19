import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.authentication.firebase_authentication import firebase_required, is_pet_owner
from api.services.pet_service import get_pet, update_pet
from api.services import lost_pet_service
from api.models import LostPetReport, Pet, User


def _active_lost_report(pet_id):
    reports = list(LostPetReport.objects.filter(pet_id=pet_id, status="active"))
    if not reports:
        return None
    return sorted(
        reports,
        key=lambda item: item.updated_at or item.created_at,
        reverse=True,
    )[0]


def _active_lost_report_data(pet_id):
    try:
        report = _active_lost_report(pet_id)
        if report is None:
            raise LostPetReport.DoesNotExist()
        return {
            "activeLostReportId": str(report.id),
            "lostReportUrl": f"petcare://lost-pets/{str(report.id)}",
            "exposeMedicalInfo": bool(getattr(report, "expose_medical_info", False)),
            "nfcNotificationsEnabled": getattr(
                report,
                "nfc_notifications_enabled",
                True,
            )
            is not False,
        }
    except Exception:
        return {
            "activeLostReportId": "",
            "lostReportUrl": "",
            "exposeMedicalInfo": False,
            "nfcNotificationsEnabled": True,
        }


def _record_scan_sighting_if_possible(pet_id, query_params):
    latitude = query_params.get("latitude") or query_params.get("lat")
    longitude = query_params.get("longitude") or query_params.get("lng")
    location = query_params.get("location") or query_params.get("locationName")

    if not latitude and not longitude and not location:
        return None

    report_data = _active_lost_report_data(pet_id)
    report_id = report_data.get("activeLostReportId")
    if not report_id:
        return None

    payload = {
        "location": location or "NFC scan location",
        "reporterName": query_params.get("reporterName") or "NFC scan",
        "reporterPhone": query_params.get("reporterPhone") or "",
        "reporterEmail": query_params.get("reporterEmail") or "",
        "note": query_params.get("note") or "Location shared from NFC scan.",
    }

    try:
        if latitude:
            payload["latitude"] = float(latitude)
        if longitude:
            payload["longitude"] = float(longitude)
    except (TypeError, ValueError):
        return None
    if query_params.get("seenAt"):
        payload["seenAt"] = query_params.get("seenAt")

    sighting, _, _ = lost_pet_service.create_sighting(report_id, payload)
    return str(sighting.id)


def _approved_lost_contact(report):
    for contact in report.emergency_contacts or []:
        if isinstance(contact, dict):
            name = contact.get("name", "")
            phone = contact.get("phone", "")
            whatsapp = contact.get("whatsapp", "")
            expose_phone = contact.get(
                "expose_phone",
                contact.get("exposePhone", False),
            )
            expose_whatsapp = contact.get(
                "expose_whatsapp",
                contact.get("exposeWhatsapp", False),
            )
        else:
            name = getattr(contact, "name", "")
            phone = getattr(contact, "phone", "")
            whatsapp = getattr(contact, "whatsapp", "")
            expose_phone = getattr(contact, "expose_phone", False)
            expose_whatsapp = getattr(contact, "expose_whatsapp", False)

        owner_phone = phone if expose_phone else ""
        owner_whatsapp = whatsapp if expose_whatsapp else ""
        if not owner_phone and not owner_whatsapp:
            continue

        return {
            "ownerName": name,
            "ownerPhone": owner_phone,
            "ownerWhatsapp": owner_whatsapp,
        }
    return {"ownerName": "", "ownerPhone": "", "ownerWhatsapp": ""}


@csrf_exempt
@firebase_required
@is_pet_owner
def nfc_payload(request, pet_id):
    """
    GET /api/pets/<pet_id>/nfc-payload/

    Returns the data bundle to embed in the NFC tag.
    Requires Firebase authentication + pet ownership.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        pet   = get_pet(pet_id)
        owner = request.user  
        payload = {
            # Pet identity
            "petId":    str(pet.id),
            "petName":  pet.name,
            "species":  pet.species,
            "breed":    pet.breed,
            "knownAllergies": pet.known_allergies,
            "ownerName": owner.name,
            "ownerPhone": owner.phone,
            "appDeepLink": f"petcare://pet/{str(pet.id)}",
            **_active_lost_report_data(pet.id),

        }
        return JsonResponse(payload)

    except Pet.DoesNotExist:
        return JsonResponse({"error": "Pet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def nfc_public_read(request, pet_id):
    """
    GET /api/nfc/read/<pet_id>/

    Public — no auth required.
    Returns pet + owner contact info for anyone who scans the tag.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        pet = get_pet(pet_id)
        active_report = _active_lost_report(pet.id)
        lost_report_data = _active_lost_report_data(pet.id)
        expose_medical_info = bool(lost_report_data.get("exposeMedicalInfo"))

        # Resolve the first owner listed on the pet
        owner_data = {
            "ownerName":     "",
            "ownerPhone":    "",
            "ownerWhatsapp": "",
            "ownerInitials": "",
        }
        if active_report is not None:
            owner_data.update(_approved_lost_contact(active_report))
        elif pet.owners:
            try:
                owner = User.objects.get(id=pet.owners[0])
                owner_data = {
                    "ownerName":     owner.name,
                    "ownerPhone":    owner.phone,
                    "ownerWhatsapp": owner.phone,
                    "ownerInitials": owner.initials or "",
                }
            except User.DoesNotExist:
                pass   # owner deleted — return pet info without contact

        response = {
            "petId":   str(pet.id),
            "petName": pet.name,
            "species": pet.species,
            "breed":   pet.breed,
            "status":  pet.status or "Unknown",
            "photoUrl": pet.photo_url or "",
            "knownAllergies": pet.known_allergies if expose_medical_info else "",
            **lost_report_data,
            **owner_data,
        }
        return JsonResponse(response)

    except Pet.DoesNotExist:
        return JsonResponse({"error": "Pet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def nfc_scan_sighting(request, pet_id):
    """
    POST /api/nfc/read/<pet_id>/sighting/

    Public endpoint used immediately after an NFC scan when the scanner agrees
    to share a last-seen location, and optionally their contact profile.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body) if request.body else {}
        if payload.get("scanSource") != "nfc":
            return JsonResponse({"error": "Invalid scan source"}, status=400)
        sighting, report, _ = lost_pet_service.create_nfc_scan_sighting(
            pet_id,
            payload,
        )
        return JsonResponse({
            "lostPetSightingId": str(sighting.id),
            **_active_lost_report_data(report.pet_id),
        }, status=201)
    except LostPetReport.DoesNotExist:
        return JsonResponse({"error": "Active lost pet report not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@firebase_required
@is_pet_owner
def nfc_sync(request, pet_id):
    """
    POST /api/pets/<pet_id>/nfc-sync/

    Marks is_nfc_synced = True on the pet after the Android app
    successfully writes the tag.
    Requires Firebase authentication + pet ownership.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        pet = update_pet(pet_id, {"isNfcSynced": True})
        return JsonResponse({
            "success":      True,
            "petId":        str(pet.id),
            "isNfcSynced":  pet.is_nfc_synced,
        })
    except Pet.DoesNotExist:
        return JsonResponse({"error": "Pet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
