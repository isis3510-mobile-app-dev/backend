# HTTP views for Pet
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import pet_service
from api.serializers.pet_serializer import pet_to_dict

@csrf_exempt
def create_pet(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.create_pet(payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

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
def medical_history(request, pet_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.add_medical_record(pet_id, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # if request.method == "DELETE":
    #     try:
    #         index = int(request.GET.get("index"))
    #         pet = pet_service.remove_medical_record(pet_id, index)
    #         return JsonResponse(pet_to_dict(pet))
    #     except Exception as e:
    #         return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def vaccinations(request, pet_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.add_vaccination_event(pet_id, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # if request.method == "DELETE":
    #     try:
    #         index = int(request.GET.get("index"))
    #         pet = pet_service.remove_vaccination_event(pet_id, index)
    #         return JsonResponse(pet_to_dict(pet))
    #     except Exception as e:
    #         return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)