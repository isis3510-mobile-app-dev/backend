# HTTP views for Screen
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from api.services import screen_service
from api.serializers.screen_serializer import screen_to_dict
from api.models import Screen


@csrf_exempt
def screen_collection(request):
    """
    GET  /api/screens/  — list all screens (no auth, seeded by devs)
    POST /api/screens/  — create a screen (no auth, seeded by devs)
    """
    if request.method == "GET":
        try:
            screens = screen_service.list_screens()
            return JsonResponse([screen_to_dict(s) for s in screens], safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            screen = screen_service.create_screen(payload)
            return JsonResponse(screen_to_dict(screen), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@require_http_methods(["GET"])
def screen_detail(request, screen_id):
    """
    GET /api/screens/<screen_id>/  — get screen by ID (no auth, seeded by devs)
    """
    try:
        screen = screen_service.get_screen(screen_id)
        return JsonResponse(screen_to_dict(screen))
    except Screen.DoesNotExist:
        return JsonResponse({"error": "Screen not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
