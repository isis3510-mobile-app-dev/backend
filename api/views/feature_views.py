# HTTP views for Feature
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import feature_service
from api.serializers.feature_serializer import feature_to_dict
from api.models import Feature


@csrf_exempt
def feature_collection(request):
    """
    GET  /api/features/  — list all features
    POST /api/features/  — create a feature
    """
    if request.method == "GET":
        try:
            app_type = request.GET.get("appType")
            features = feature_service.list_features(app_type=app_type)
            return JsonResponse([feature_to_dict(f) for f in features], safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            feature = feature_service.create_feature(payload)
            return JsonResponse(feature_to_dict(feature), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def feature_detail(request, feature_id):
    """
    GET    /api/features/<feature_id>/  — get feature by ID
    PUT    /api/features/<feature_id>/  — full update
    DELETE /api/features/<feature_id>/  — delete feature
    """
    if request.method == "GET":
        try:
            feature = feature_service.get_feature(feature_id)
            return JsonResponse(feature_to_dict(feature))
        except Feature.DoesNotExist:
            return JsonResponse({"error": "Feature not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "PUT":
        try:
            payload = json.loads(request.body)
            feature = feature_service.update_feature(feature_id, payload)
            return JsonResponse(feature_to_dict(feature))
        except Feature.DoesNotExist:
            return JsonResponse({"error": "Feature not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            feature_service.delete_feature(feature_id)
            return JsonResponse({}, status=204)
        except Feature.DoesNotExist:
            return JsonResponse({"error": "Feature not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)
