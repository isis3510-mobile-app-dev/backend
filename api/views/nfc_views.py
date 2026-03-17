import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.authentication.firebase_authentication import firebase_required, is_pet_owner
from api.services.pet_service import get_pet, update_pet
from api.models import Pet, User

@csrf_exempt
@firebase_required
@is_pet_owner
def nfc_payload(request, pet_id):
    """
    GET /api/pets/<pet_id>/nfc-payload/

    Returns the data bundle to embed in the NFC tag.
    Requires Firebase authentication + pet ownership.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        pet   = get_pet(pet_id)
        owner = request.user  
        payload = {
            # Pet identity
            "petId":    str(pet.id),
            "petName":  pet.name,
            "species":  pet.species,
            "breed":    pet.breed,
            "knownAllergies": pet.known_allergies,
            "ownerName": owner.name,
            "ownerPhone": owner.phone,
            "appDeepLink": f"petcare://pet/{str(pet.id)}" 

        }
        return JsonResponse(payload)

    except Pet.DoesNotExist:
        return JsonResponse({"error": "Pet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def nfc_public_read(request, pet_id):
    """
    GET /api/nfc/read/<pet_id>/

    Public — no auth required.
    Returns pet + owner contact info for anyone who scans the tag.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        pet = get_pet(pet_id)

        # Resolve the first owner listed on the pet
        owner_data = {
            "ownerName":     "",
            "ownerPhone":    "",
            "ownerInitials": "",
        }
        if pet.owners:
            try:
                owner = User.objects.get(id=pet.owners[0])
                owner_data = {
                    "ownerName":     owner.name,
                    "ownerPhone":    owner.phone,
                    "ownerInitials": owner.initials or "",
                }
            except User.DoesNotExist:
                pass   # owner deleted — return pet info without contact

        response = {
            "petId":   str(pet.id),
            "petName": pet.name,
            "species": pet.species,
            "breed":   pet.breed,
            "status":  pet.status or "Unknown",
            "photoUrl": pet.photo_url or "",
            "knownAllergies": pet.known_allergies,
            "defaultVet": pet.default_vet,
            "defaultClinic": pet.default_clinic,
            **owner_data,
        }
        return JsonResponse(response)

    except Pet.DoesNotExist:
        return JsonResponse({"error": "Pet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@firebase_required
@is_pet_owner
def nfc_sync(request, pet_id):
    """
    POST /api/pets/<pet_id>/nfc-sync/

    Marks is_nfc_synced = True on the pet after the Android app
    successfully writes the tag.
    Requires Firebase authentication + pet ownership.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        pet = update_pet(pet_id, {"isNfcSynced": True})
        return JsonResponse({
            "success":      True,
            "petId":        str(pet.id),
            "isNfcSynced":  pet.is_nfc_synced,
        })
    except Pet.DoesNotExist:
        return JsonResponse({"error": "Pet not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)