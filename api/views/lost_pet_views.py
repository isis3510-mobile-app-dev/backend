import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.authentication.firebase_authentication import firebase_required, is_pet_owner
from api.models.lost_pet import LostPetReport
from api.serializers.lost_pet_serializer import (
    lost_pet_report_card_to_dict,
    lost_pet_report_detail_to_dict,
    lost_pet_report_owner_to_dict,
)
from api.services import lost_pet_service


def _json_payload(request):
    if not request.body:
        return {}
    return json.loads(request.body)


@csrf_exempt
def public_lost_pet_collection(request):
    if request.method == "GET":
        reports = lost_pet_service.list_active_reports_with_pets()
        return JsonResponse(
            [lost_pet_report_card_to_dict(report, pet) for report, pet in reports],
            safe=False,
        )

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def public_lost_pet_detail(request, report_id):
    if request.method == "GET":
        try:
            report, pet = lost_pet_service.get_public_report(report_id)
            return JsonResponse(lost_pet_report_detail_to_dict(report, pet))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
@is_pet_owner
def pet_lost_report(request, pet_id):
    if request.method == "GET":
        try:
            report, pet = lost_pet_service.get_report_for_pet(pet_id)
            return JsonResponse(lost_pet_report_owner_to_dict(report, pet))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "POST":
        try:
            payload = _json_payload(request)
            report, pet = lost_pet_service.create_or_reactivate_report(
                pet_id,
                request.user.id,
                payload,
            )
            return JsonResponse(lost_pet_report_owner_to_dict(report, pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "PUT":
        try:
            payload = _json_payload(request)
            report, pet = lost_pet_service.update_report_for_pet(pet_id, payload)
            return JsonResponse(lost_pet_report_owner_to_dict(report, pet))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
@is_pet_owner
def mark_pet_found(request, pet_id):
    if request.method == "POST":
        try:
            report, pet = lost_pet_service.mark_pet_found(pet_id)
            payload = {
                "petId": str(pet.id),
                "petStatus": pet.status,
                "report": lost_pet_report_owner_to_dict(report, pet) if report else None,
            }
            return JsonResponse(payload)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

def sighting_to_dict(sighting):
    return {
        "id": str(sighting.id),
        "reportId": str(sighting.report_id),
        "petId": str(sighting.pet_id),
        "location": sighting.location,
        "latitude": sighting.latitude,
        "longitude": sighting.longitude,
        "note": sighting.note,
        "photoUrl": sighting.photo_url,
        "seenAt": sighting.seen_at,
        "reporterName": sighting.reporter_name,
        "reporterPhone": sighting.reporter_phone,
        "reporterEmail": sighting.reporter_email,
        "createdAt": sighting.created_at,
    }


@csrf_exempt
def create_sighting_view(request, report_id):

    if request.method == "GET":
        try:
            sightings, report = lost_pet_service.list_sightings_for_report(report_id)

            return JsonResponse(
                [sighting_to_dict(s) for s in sightings],
                safe=False
            )

        except LostPetReport.DoesNotExist:
            return JsonResponse({"error": "Report not found"}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
    #POST /api/lost-pets/<report_id>/sighting/
    
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = _json_payload(request)  # ✅ usar helper consistente

        sighting, report, pet = lost_pet_service.create_sighting(
            report_id,
            payload
        )

        return JsonResponse({
            "lostPetSightingId": str(sighting.id),
            "reportId": str(report.id),
            "petId": str(pet.id),
            "message": "Sighting created successfully"
        }, status=201)

    except LostPetReport.DoesNotExist:
        return JsonResponse({"error": "Report not found"}, status=404)

    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
