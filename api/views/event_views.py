import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import event_service
from api.serializers.event_serializer import event_to_dict
from api.authentication.firebase_authentication import firebase_required


@csrf_exempt
@firebase_required
def event_collection(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            event = event_service.create_event(payload)
            return JsonResponse(event_to_dict(event), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "GET":
        filters = {}
        pet_id   = request.GET.get("pet_id")
        owner_id = request.GET.get("owner_id")

        if pet_id:
            # Verify the requested pet belongs to the authenticated user
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if pet_id not in user_pet_ids:
                return JsonResponse({"error": "Not authorized to access this pet's events"}, status=403)
            filters["pet_id"] = pet_id

        elif owner_id:
            # Only allow fetching own events
            if owner_id != str(request.user.id):
                return JsonResponse({"error": "Not authorized"}, status=403)
            filters["owner_id"] = owner_id

        else:
            # No filter provided — return events only for the user's own pets
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if not user_pet_ids:
                return JsonResponse([], safe=False)
            events = event_service.list_events_for_pets(user_pet_ids)
            return JsonResponse([event_to_dict(e) for e in events], safe=False)

        events = event_service.list_events(filters)
        return JsonResponse([event_to_dict(e) for e in events], safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
def event_detail(request, event_id):
    if request.method == "GET":
        try:
            event = event_service.get_event(event_id)
            # Verify the event belongs to a pet owned by the user
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if str(event.pet_id) not in user_pet_ids:
                return JsonResponse({"error": "Not authorized"}, status=403)
            return JsonResponse(event_to_dict(event))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "PUT":
        try:
            event = event_service.get_event(event_id)
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if str(event.pet_id) not in user_pet_ids:
                return JsonResponse({"error": "Not authorized"}, status=403)
            payload = json.loads(request.body)
            event = event_service.update_event(event_id, payload)
            return JsonResponse(event_to_dict(event))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            event = event_service.get_event(event_id)
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if str(event.pet_id) not in user_pet_ids:
                return JsonResponse({"error": "Not authorized"}, status=403)
            event_service.delete_event(event_id)
            return JsonResponse({}, status=204)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
def event_documents(request, event_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            event = event_service.add_document_to_event(event_id, payload)
            return JsonResponse(event_to_dict(event), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)