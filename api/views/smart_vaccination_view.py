
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from api.models import Pet
from api.services.smart_vaccination_service import analyze_pet_vaccines
from api.serializers.smart_vaccination_serializer import smart_response_to_dict

@csrf_exempt
@require_http_methods(["GET"])
def pet_smart_view(request, pet_id):
    try:
        pet, suggestions = analyze_pet_vaccines(pet_id)
        return JsonResponse(smart_response_to_dict(pet, suggestions))
    except Pet.DoesNotExist:
        return JsonResponse({"error": "Pet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)