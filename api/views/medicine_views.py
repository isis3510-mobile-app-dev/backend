import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.authentication.firebase_authentication import firebase_required
from api.serializers.medicine_serializer import medicine_to_dict
from api.services import medicine_service


@csrf_exempt
@firebase_required
def medicine_collection(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            medicine = medicine_service.create_medicine(request.user, payload)
            return JsonResponse(medicine_to_dict(medicine), status=201)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "GET":
        filters = {}
        pet_id = request.GET.get("pet_id")
        owner_id = request.GET.get("owner_id")

        if pet_id:
            # Verify the requested pet belongs to the authenticated user
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if pet_id not in user_pet_ids:
                return JsonResponse({"error": "Not authorized to access this pet's medicines"}, status=403)
            filters["pet_id"] = pet_id

        elif owner_id:
            # Only allow fetching own medicines
            if owner_id != str(request.user.id):
                return JsonResponse({"error": "Not authorized"}, status=403)
            filters["owner_id"] = owner_id

        else:
            # No filter provided — return medicines only for the user's own pets
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if not user_pet_ids:
                return JsonResponse([], safe=False)
            medicines = medicine_service.list_medicines_for_pets(user_pet_ids)
            return JsonResponse([medicine_to_dict(m) for m in medicines], safe=False)

        medicines = medicine_service.list_medicines(filters)
        return JsonResponse([medicine_to_dict(m) for m in medicines], safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
def medicine_detail(request, medicine_id):
    if request.method == "GET":
        try:
            medicine = medicine_service.get_medicine(medicine_id)
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if str(medicine.pet_id) not in user_pet_ids:
                return JsonResponse({"error": "Not authorized"}, status=403)
            return JsonResponse(medicine_to_dict(medicine))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "PUT":
        try:
            medicine = medicine_service.get_medicine(medicine_id)
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if str(medicine.pet_id) not in user_pet_ids:
                return JsonResponse({"error": "Not authorized"}, status=403)
            payload = json.loads(request.body)
            medicine = medicine_service.update_medicine(medicine_id, payload)
            return JsonResponse(medicine_to_dict(medicine))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            medicine = medicine_service.get_medicine(medicine_id)
            user_pet_ids = [str(pid) for pid in request.user.pets]
            if str(medicine.pet_id) not in user_pet_ids:
                return JsonResponse({"error": "Not authorized"}, status=403)
            medicine_service.delete_medicine(medicine_id)
            return JsonResponse({}, status=204)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    return JsonResponse({"error": "Method not allowed"}, status=405)