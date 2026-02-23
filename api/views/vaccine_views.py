# HTTP views for Vaccine
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from api.services.vaccine_service import (
    create_vaccine,
    get_vaccine,
    update_vaccine,
    delete_vaccine,
)
from api.serializers.vaccine_serializer import vaccine_to_dict
from api.models import Vaccine

@csrf_exempt
@require_http_methods(["POST"])
def create_vaccine_view(request):
    try:
        data = json.loads(request.body)
        vaccine = create_vaccine(data)
        return JsonResponse(vaccine_to_dict(vaccine), status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def get_vaccine_view(request, vaccine_id):
    try:
        vaccine = get_vaccine(vaccine_id)
        return JsonResponse(vaccine_to_dict(vaccine))
    except Vaccine.DoesNotExist:
        return JsonResponse({"error": "Vaccine not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["PUT"])
def update_vaccine_view(request, vaccine_id):
    try:
        data = json.loads(request.body)
        vaccine = update_vaccine(vaccine_id, data)
        return JsonResponse(vaccine_to_dict(vaccine))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Vaccine.DoesNotExist:
        return JsonResponse({"error": "Vaccine not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_vaccine_view(request, vaccine_id):
    try:
        delete_vaccine(vaccine_id)
        return JsonResponse({"message": "Vaccine deleted"}, status=204)
    except Vaccine.DoesNotExist:
        return JsonResponse({"error": "Vaccine not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def list_vaccines_view(request):
    try:
        vaccines = Vaccine.objects.all()
        return JsonResponse([vaccine_to_dict(v) for v in vaccines], safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)