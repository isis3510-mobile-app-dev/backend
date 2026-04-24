import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.authentication.firebase_authentication import firebase_required
from api.serializers.weight_log_serializer import weight_log_to_dict
from api.services import weight_log_service


@csrf_exempt
@firebase_required
def weight_log_collection(request, pet_id):
    if request.method == "GET":
        try:
            logs = weight_log_service.list_weight_logs(request.user, pet_id)
            return JsonResponse([weight_log_to_dict(log) for log in logs], safe=False)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            log = weight_log_service.create_weight_log(request.user, pet_id, payload)
            return JsonResponse(weight_log_to_dict(log), status=201)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
def weight_log_detail(request, pet_id, weight_log_id):
    if request.method == "GET":
        try:
            log = weight_log_service.get_weight_log(request.user, pet_id, weight_log_id)
            return JsonResponse(weight_log_to_dict(log))
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "PUT":
        try:
            payload = json.loads(request.body)
            log = weight_log_service.update_weight_log(request.user, pet_id, weight_log_id, payload)
            return JsonResponse(weight_log_to_dict(log))
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            weight_log_service.delete_weight_log(request.user, pet_id, weight_log_id)
            return HttpResponse(status=204)
        except PermissionError as e:
            return JsonResponse({"error": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    return JsonResponse({"error": "Method not allowed"}, status=405)
