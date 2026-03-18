import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import pet_service
from api.serializers.pet_serializer import _to_object_id, pet_to_dict, vaccination_to_api_dict, vaccination_to_dict
from api.authentication.firebase_authentication import firebase_required, is_pet_owner

@csrf_exempt
@firebase_required
def pet_collection(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.create_pet(request.user, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    elif request.method == "GET":
        pets = pet_service.list_pets()
        pets_data = [pet_to_dict(pet) for pet in pets]
        return JsonResponse(pets_data, safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
def my_pets(request):
    if request.method == "GET":
        pets = pet_service.list_pets_by_owner(request.user.id)
        pets_data = [pet_to_dict(pet) for pet in pets]
        return JsonResponse(pets_data, safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
@is_pet_owner
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
@firebase_required
@is_pet_owner
def vaccinations(request, pet_id):
    if request.method == "GET":
        vaccinations = pet_service.list_vaccinations(pet_id)
        return JsonResponse([vaccination_to_api_dict(v) for v in vaccinations], status=200, safe=False)

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.add_vaccination(pet_id, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
@firebase_required
@is_pet_owner
def vaccination_detail(request, pet_id, vaccination_id):
    if request.method == "GET":
        pet = pet_service.get_pet(pet_id)
        if not pet:
            return JsonResponse({"error": "Pet not found"}, status=404)
        target_id = _to_object_id(vaccination_id)
        for v in (pet.vaccinations or []):
            v_dict = vaccination_to_dict(v)
            if pet_service._ids_equal(v_dict.get("_id"), target_id):
                return JsonResponse(vaccination_to_api_dict(v_dict))
        return JsonResponse({"error": "Vaccination not found"}, status=404)
            
    if request.method == "PUT":
        try:
            payload = json.loads(request.body)
            # Check if trying to update dateGiven
            if "newDateGiven" in payload and "dateGiven" in payload:
                # User wants to change the date
                pet = pet_service.update_vaccination_date(
                    pet_id, 
                    payload["vaccineId"], 
                    payload["dateGiven"],
                    payload["newDateGiven"]
                )
                # If there are other fields to update, update them too
                if len(payload) > 3:  # More than vaccineId, dateGiven, newDateGiven
                    remaining = {k: v for k, v in payload.items() if k not in ("vaccineId", "dateGiven", "newDateGiven")}
                    remaining["vaccineId"] = payload["vaccineId"]
                    remaining["dateGiven"] = payload["newDateGiven"]
                    pet = pet_service.update_vaccination(pet_id, remaining)
            else:
                pet = pet_service.update_vaccination(pet_id, payload)
            pet = pet_service.update_vaccination(pet_id, vaccination_id, payload)
            return JsonResponse(pet_to_dict(pet))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            pet = pet_service.delete_vaccination(pet_id, vaccination_id)
            return JsonResponse(pet_to_dict(pet))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
@is_pet_owner
def vaccination_documents(request, pet_id, vaccination_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            pet = pet_service.add_document_to_vaccination(pet_id, vaccination_id, payload)
            return JsonResponse(pet_to_dict(pet), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)
