import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.authentication.firebase_authentication import firebase_required, is_pet_owner
from api.serializers.exercise_serializer import exercise_to_dict
from api.services import exercise_service


@csrf_exempt
@firebase_required
@is_pet_owner
def exercise_collection(request, pet_id):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            exercise = exercise_service.create_exercise(request.user, pet_id, payload)
            return JsonResponse(exercise_to_dict(exercise), status=201)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "GET":
        try:
            exercises = exercise_service.list_exercises(request.user, pet_id)
            return JsonResponse([exercise_to_dict(e) for e in exercises], safe=False)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
@is_pet_owner
def exercise_detail(request, exercise_id, pet_id):
    if request.method == "GET":
        try:
            exercise = exercise_service.get_exercise(request.user, pet_id, exercise_id)
            return JsonResponse(exercise_to_dict(exercise))
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "PUT":
        try:
            payload = json.loads(request.body)
            exercise = exercise_service.update_exercise(request.user, pet_id, exercise_id, payload)
            return JsonResponse(exercise_to_dict(exercise))
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            exercise_service.delete_exercise(request.user, pet_id, exercise_id)
            return HttpResponse(status=204)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    return JsonResponse({"error": "Method not allowed"}, status=405)
