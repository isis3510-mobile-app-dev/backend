# HTTP views for ScreenTimeLog
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import screen_time_log_service
from api.serializers.screen_time_log_serializer import screen_time_log_to_dict
from api.authentication.firebase_authentication import firebase_required


@csrf_exempt
def screen_time_log_collection(request):
    """
    GET  /api/screen-time-logs/  — list logs, no auth (used by analytics pipeline)
        optional query params: ?userId=<id>&screenId=<id>

    POST /api/screen-time-logs/  — create a log entry, requires Firebase auth
    """
    if request.method == "GET":
        try:
            user_id = request.GET.get("userId")
            screen_id = request.GET.get("screenId")
            logs = screen_time_log_service.list_logs(user_id=user_id, screen_id=screen_id)
            return JsonResponse([screen_time_log_to_dict(log) for log in logs], safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    if request.method == "POST":
        return _create_log(request)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@firebase_required
def _create_log(request):
    try:
        payload = json.loads(request.body)
        log = screen_time_log_service.create_log(payload)
        return JsonResponse(screen_time_log_to_dict(log), status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
