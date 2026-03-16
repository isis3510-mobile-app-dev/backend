import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.services import feature_route_service
from api.serializers.feature_route_serializer import feature_route_to_dict
from api.models import FeatureRoute


@csrf_exempt
def feature_route_collection(request):
    """
    GET  /api/feature-routes/  — list all feature routes
    POST /api/feature-routes/  — create a feature route
    """
    if request.method == "GET":
        try:
            routes = feature_route_service.list_feature_routes()
            return JsonResponse([feature_route_to_dict(r) for r in routes], safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            route = feature_route_service.create_feature_route(payload)
            return JsonResponse(feature_route_to_dict(route), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def feature_route_detail(request, route_id):
    """
    GET    /api/feature-routes/<route_id>/  — get route by ID
    PUT    /api/feature-routes/<route_id>/  — full update
    DELETE /api/feature-routes/<route_id>/  — delete route
    """
    if request.method == "GET":
        try:
            route = feature_route_service.get_feature_route(route_id)
            return JsonResponse(feature_route_to_dict(route))
        except FeatureRoute.DoesNotExist:
            return JsonResponse({"error": "FeatureRoute not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "PUT":
        try:
            payload = json.loads(request.body)
            route = feature_route_service.update_feature_route(route_id, payload)
            return JsonResponse(feature_route_to_dict(route))
        except FeatureRoute.DoesNotExist:
            return JsonResponse({"error": "FeatureRoute not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    if request.method == "DELETE":
        try:
            feature_route_service.delete_feature_route(route_id)
            return JsonResponse({}, status=204)
        except FeatureRoute.DoesNotExist:
            return JsonResponse({"error": "FeatureRoute not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)
