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
        pet_id = request.GET.get("pet_id")
        owner_id = request.GET.get("owner_id")
        if pet_id:
            filters["pet_id"] = pet_id
        if owner_id:
            filters["owner_id"] = owner_id
        events = event_service.list_events(filters if filters else None)
        events_data = [event_to_dict(e) for e in events]
        return JsonResponse(events_data, safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
def event_detail(request, event_id):
    if request.method == "GET":
        try:
            event = event_service.get_event(event_id)
            return JsonResponse(event_to_dict(event))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "PUT":
        try:
            payload = json.loads(request.body)
            event = event_service.update_event(event_id, payload)
            return JsonResponse(event_to_dict(event))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        event_service.delete_event(event_id)
        return JsonResponse({}, status=204)

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
