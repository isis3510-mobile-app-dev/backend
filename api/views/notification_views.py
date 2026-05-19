import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import notification_service
from api.serializers.notification_serializer import notification_to_dict
from api.authentication.firebase_authentication import firebase_required


@csrf_exempt
@firebase_required
def notification_collection(request):
    if request.method == "POST":
        return JsonResponse(
            {"error": "Notification creation is handled by backend services."},
            status=405,
        )

    elif request.method == "GET":
        filters = {"user_id": request.user.id}
        notifications = notification_service.list_notifications(filters)
        notifications_data = [notification_to_dict(n) for n in notifications]
        return JsonResponse(notifications_data, safe=False)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@firebase_required
def notification_detail(request, notification_id):
    if request.method == "GET":
        try:
            notification = notification_service.get_notification(notification_id)
            if str(notification.user_id) != str(request.user.id):
                return JsonResponse({"error": "Not found"}, status=404)
            return JsonResponse(notification_to_dict(notification))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)

    if request.method == "PUT":
        try:
            existing = notification_service.get_notification(notification_id)
            if str(existing.user_id) != str(request.user.id):
                return JsonResponse({"error": "Not found"}, status=404)
            payload = json.loads(request.body)
            payload.pop("userId", None)
            payload.pop("user_id", None)
            notification = notification_service.update_notification(notification_id, payload)
            return JsonResponse(notification_to_dict(notification))
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            existing = notification_service.get_notification(notification_id)
            if str(existing.user_id) != str(request.user.id):
                return JsonResponse({"error": "Not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=404)
        notification_service.delete_notification(notification_id)
        return JsonResponse({}, status=204)

    return JsonResponse({"error": "Method not allowed"}, status=405)
