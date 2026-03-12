import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import pet_service
from api.serializers.pet_serializer import pet_to_dict

@csrf_exempt
def pet_collection(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.create_pet(payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method == "GET":
        pets = pet_service.list_pets()
        pets_data = [pet_to_dict(pet) for pet in pets]
        return JsonResponse(pets_data, safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def pet_detail(request, pet_id):
    if request.method == "GET":
        pet = pet_service.get_pet(pet_id)
        if not pet:
            return JsonResponse({"error": "Pet not found"}, status=404)
        return JsonResponse(pet_to_dict(pet))

    if request.method == "PUT":
        try:
            payload = json.loads(request.body)
            pet = pet_service.update_pet(pet_id, payload)
            return JsonResponse(pet_to_dict(pet))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        pet_service.delete_pet(pet_id)
        return JsonResponse({}, status=204)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def events(request, pet_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.add_event(pet_id, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # if request.method == "DELETE":
    #     try:
    #         event_id = request.GET.get("event_id")
    #         pet = pet_service.remove_medical_record(pet_id, event_id)
    #         return JsonResponse(pet_to_dict(pet))
    #     except Exception as e:
    #         return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def vaccinations(request, pet_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.add_vaccination(pet_id, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def notifications(request, pet_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.add_notification(pet_id, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def documents(request, pet_id, record_type, record_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            if record_type == "vaccination":
                pet = pet_service.add_document_to_vaccination(pet_id, record_id, payload)
            elif record_type == "event":
                pet = pet_service.add_document_to_event(pet_id, record_id, payload)
            else:
                return JsonResponse({"error": "Invalid record type"}, status=400)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)