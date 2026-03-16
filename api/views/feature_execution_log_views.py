import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import feature_execution_log_service
from api.serializers.feature_execution_log_serializer import feature_execution_log_to_dict
from api.authentication.firebase_authentication import firebase_required


@csrf_exempt
def feature_execution_log_collection(request):
    """
    GET  /api/feature-execution-logs/  — list logs, no auth (analytics pipeline)
        optional query params: ?userId=<id>&featureId=<id>
    POST /api/feature-execution-logs/  — create a log entry, requires Firebase auth
    """
    if request.method == "GET":
        try:
            user_id = request.GET.get("userId")
            feature_id = request.GET.get("featureId")
            logs = feature_execution_log_service.list_logs(
                user_id=user_id, feature_id=feature_id
            )
            return JsonResponse(
                [feature_execution_log_to_dict(log) for log in logs], safe=False
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    if request.method == "POST":
        return _create_execution_log(request)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@firebase_required
def _create_execution_log(request):
    """Inner handler for POST — enforces Firebase auth."""
    try:
        payload = json.loads(request.body)
        log = feature_execution_log_service.create_log(payload)
        return JsonResponse(feature_execution_log_to_dict(log), status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
