import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from bson import ObjectId
from datetime import date, datetime, timezone

from api.views.pet_views import (
    pet_collection,
    my_pets,
    pet_detail,
    vaccinations,
    vaccination_documents,
)
from api.models import Pet, Vaccination, AttachedDocument
from api.services import pet_service
from api.serializers.pet_serializer import pet_to_dict, format_date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PET_ID = str(ObjectId())
USER_ID = str(ObjectId())
VACCINE_OBJ_ID = str(ObjectId())
DOC_OBJ_ID = str(ObjectId())


def _make_attached_doc(**kwargs):
    doc = MagicMock(spec=AttachedDocument)
    doc.document_id = kwargs.get("document_id", DOC_OBJ_ID)
    doc.file_name = kwargs.get("file_name", "record.pdf")
    doc.file_uri = kwargs.get("file_uri", "https://storage.example.com/record.pdf")
    return doc


def _make_vaccination(**kwargs):
    v = MagicMock(spec=Vaccination)
    v.vaccine_id = kwargs.get("vaccine_id", VACCINE_OBJ_ID)
    v.date_given = kwargs.get("date_given", date(2026, 1, 15))
    v.next_due_date = kwargs.get("next_due_date", date(2027, 1, 15))
    v.lot_number = kwargs.get("lot_number", "LOT123")
    v.status = kwargs.get("status", "completed")
    v.administered_by = kwargs.get("administered_by", "Dr. Smith")
    v.clinic_name = kwargs.get("clinic_name", "Happy Paws")
    v.attached_documents = kwargs.get("attached_documents", [])
    return v


def _make_pet(**kwargs):
    p = MagicMock(spec=Pet)
    p.id = ObjectId(PET_ID)
    p.schema = kwargs.get("schema", 1)
    p.owners = kwargs.get("owners", [USER_ID])
    p.name = kwargs.get("name", "Buddy")
    p.species = kwargs.get("species", "dog")
    p.breed = kwargs.get("breed", "Labrador")
    p.gender = kwargs.get("gender", "male")
    p.birth_date = kwargs.get("birth_date", date(2022, 5, 10))
    p.weight = kwargs.get("weight", 25.50)
    p.color = kwargs.get("color", "golden")
    p.photo_url = kwargs.get("photo_url", "https://example.com/buddy.jpg")
    p.status = kwargs.get("status", "healthy")
    p.is_nfc_synced = kwargs.get("is_nfc_synced", False)
    p.known_allergies = kwargs.get("known_allergies", "")
    p.default_vet = kwargs.get("default_vet", "Dr. Smith")
    p.default_clinic = kwargs.get("default_clinic", "Happy Paws")
    p.vaccinations = kwargs.get("vaccinations", [])
    return p


def _auth_request(factory, method, path, payload=None, token="valid_token"):
    """Build a request with an HTTP_AUTHORIZATION header."""
    body = json.dumps(payload) if payload else ""
    maker = getattr(factory, method)
    return maker(
        path,
        body,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _mock_firebase_auth(mock_auth, mock_user):
    """Set up mock Firebase auth for the firebase_required decorator."""
    mock_auth.verify_id_token.return_value = {"uid": mock_user.firebase_uid}


# ===========================================================================
# Pet Service Tests
# ===========================================================================

class TestPetService(TestCase):

    @patch("api.services.pet_service.Pet")
    def test_create_pet(self, MockPet):
        mock_user = MagicMock()
        mock_user.id = ObjectId(USER_ID)
        mock_user.pets = []
        
        created = _make_pet(name="Luna", owners=[mock_user.id])
        MockPet.objects.create.return_value = created
        MockPet.objects.get.return_value = created
        # Payload uses camelCase (as the API receives)
        data = {"name": "Luna", "species": "cat", "breed": "Siamese"}
        result = pet_service.create_pet(mock_user, data)
        self.assertEqual(result.name, "Luna")
        MockPet.objects.create.assert_called_once()
        mock_user.save.assert_called_once()
        self.assertIn(created.id, mock_user.pets)

    @patch("api.services.pet_service.Pet")
    def test_list_pets(self, MockPet):
        MockPet.objects.all.return_value = [_make_pet(), _make_pet(name="Luna")]
        result = pet_service.list_pets()
        self.assertEqual(len(result), 2)
        MockPet.objects.all.assert_called_once()

    @patch("api.services.pet_service.Pet")
    def test_get_pet(self, MockPet):
        expected = _make_pet()
        MockPet.objects.get.return_value = expected
        result = pet_service.get_pet(PET_ID)
        self.assertEqual(result, expected)
        MockPet.objects.get.assert_called_once_with(id=PET_ID)

    @patch("api.services.pet_service.Pet")
    def test_update_pet(self, MockPet):
        pet = _make_pet(name="OldName")
        updated = _make_pet(name="NewName")
        MockPet.objects.get.side_effect = [pet, updated]
        result = pet_service.update_pet(PET_ID, {"name": "NewName"})
        pet.save.assert_called_once()
        self.assertEqual(result.name, "NewName")

    @patch("api.services.pet_service.Pet")
    def test_delete_pet(self, MockPet):
        MockPet.objects.filter.return_value.delete.return_value = None
        pet_service.delete_pet(PET_ID)
        MockPet.objects.filter.assert_called_once_with(id=PET_ID)
        MockPet.objects.filter.return_value.delete.assert_called_once()

    @patch("api.services.pet_service.Pet")
    def test_add_vaccination(self, MockPet):
        pet = _make_pet(vaccinations=None)
        updated = _make_pet(vaccinations=[_make_vaccination()])
        MockPet.objects.get.side_effect = [pet, updated]
        # Payload uses camelCase keys (API input)
        data = {
            "vaccineId": VACCINE_OBJ_ID,
            "dateGiven": "2026-01-15",
            "status": "completed",
        }
        result = pet_service.add_vaccination(PET_ID, data)
        pet.save.assert_called_once()
        self.assertEqual(len(result.vaccinations), 1)

    @patch("api.services.pet_service.Pet")
    def test_add_document_to_vaccination(self, MockPet):
        vacc = _make_vaccination(attached_documents=None)
        pet = _make_pet(vaccinations=[vacc])
        updated_pet = _make_pet(vaccinations=[_make_vaccination(attached_documents=[_make_attached_doc()])])
        MockPet.objects.get.side_effect = [pet, updated_pet]
        # Payload uses camelCase keys (API input)
        doc_data = {
            "documentId": DOC_OBJ_ID,
            "fileName": "record.pdf",
            "fileUri": "https://storage.example.com/record.pdf",
        }
        result = pet_service.add_document_to_vaccination(PET_ID, VACCINE_OBJ_ID, doc_data)
        pet.save.assert_called_once()

    @patch("api.services.pet_service.Pet")
    def test_update_vaccination(self, MockPet):
        existing = {
            "vaccine_id": ObjectId(VACCINE_OBJ_ID),
            "date_given": datetime(2026, 1, 15),
            "status": "completed",
            "clinic_name": "Old Clinic",
        }
        pet = _make_pet(vaccinations=[existing])
        updated = _make_pet(vaccinations=[{**existing, "status": "pending", "clinic_name": "New Clinic"}])
        MockPet.objects.get.side_effect = [pet, updated]
        payload = {
            "vaccineId": VACCINE_OBJ_ID,
            "dateGiven": "2026-01-15",
            "status": "pending",
            "clinicName": "New Clinic",
        }
        result = pet_service.update_vaccination(PET_ID, payload)
        pet.save.assert_called_once()
        self.assertEqual(result.vaccinations[0]["status"], "pending")
        self.assertEqual(result.vaccinations[0]["clinic_name"], "New Clinic")

    @patch("api.services.pet_service.Pet")
    def test_update_vaccination_not_found(self, MockPet):
        pet = _make_pet(vaccinations=[])
        MockPet.objects.get.return_value = pet
        payload = {
            "vaccineId": VACCINE_OBJ_ID,
            "dateGiven": "2026-01-15",
            "status": "pending",
        }
        with self.assertRaises(Exception):
            pet_service.update_vaccination(PET_ID, payload)

    @patch("api.services.pet_service.Pet")
    def test_delete_vaccination(self, MockPet):
        existing = {
            "vaccine_id": ObjectId(VACCINE_OBJ_ID),
            "date_given": datetime(2026, 1, 15),
            "status": "completed",
        }
        pet = _make_pet(vaccinations=[existing])
        updated = _make_pet(vaccinations=[])
        MockPet.objects.get.side_effect = [pet, updated]
        payload = {
            "vaccineId": VACCINE_OBJ_ID,
            "dateGiven": "2026-01-15",
        }
        result = pet_service.delete_vaccination(PET_ID, payload)
        pet.save.assert_called_once()
        self.assertEqual(result.vaccinations, [])

    @patch("api.services.pet_service.Pet")
    def test_delete_vaccination_not_found(self, MockPet):
        pet = _make_pet(vaccinations=[])
        MockPet.objects.get.return_value = pet
        payload = {
            "vaccineId": VACCINE_OBJ_ID,
            "dateGiven": "2026-01-15",
        }
        with self.assertRaises(Exception):
            pet_service.delete_vaccination(PET_ID, payload)

    def test_parse_payload_dates_converts_strings(self):
        # Internal snake_case keys (after translation)
        data = {
            "birth_date": "2022-05-10T00:00:00Z",
            "name": "Buddy",
        }
        result = pet_service.parse_payload_dates(data)
        self.assertIsInstance(result["birth_date"], datetime)
        self.assertEqual(result["name"], "Buddy")

    def test_parse_payload_dates_nested(self):
        data = {
            "vaccinations": [
                {"date_given": "2026-01-15T00:00:00Z", "lot_number": "LOT1"}
            ]
        }
        result = pet_service.parse_payload_dates(data)
        self.assertIsInstance(result["vaccinations"][0]["date_given"], datetime)

    def test_parse_payload_dates_none_value(self):
        data = {"birth_date": None, "name": "Buddy"}
        result = pet_service.parse_payload_dates(data)
        self.assertIsNone(result["birth_date"])


# ===========================================================================
# Pet View Tests
# ===========================================================================

class TestPetViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _setup_auth_mocks(self, mock_auth, firebase_uid="uid123"):
        from api.models import User
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = firebase_uid
        mock_user.pets = [ObjectId(PET_ID)]
        mock_auth.verify_id_token.return_value = {"uid": firebase_uid}
        return mock_user

    # --- GET /api/pets/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_list_pets_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.list_pets.return_value = [_make_pet()]
            req = _auth_request(self.factory, "get", "/api/pets/")
            resp = pet_collection(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["name"], "Buddy")

    def test_list_pets_no_auth_returns_401(self):
        req = self.factory.get("/api/pets/")
        resp = pet_collection(req)
        self.assertEqual(resp.status_code, 401)

    # --- GET /api/pets/mine/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_my_pets_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.list_pets_by_owner.return_value = [_make_pet()]
            req = _auth_request(self.factory, "get", "/api/pets/mine/")
            resp = my_pets(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["name"], "Buddy")
        mock_svc.list_pets_by_owner.assert_called_once_with(mock_user.id)

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_my_pets_empty_list(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.list_pets_by_owner.return_value = []
            req = _auth_request(self.factory, "get", "/api/pets/mine/")
            resp = my_pets(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), [])

    def test_my_pets_no_auth_returns_401(self):
        req = self.factory.get("/api/pets/mine/")
        resp = my_pets(req)
        self.assertEqual(resp.status_code, 401)

    def test_my_pets_method_not_allowed(self):
        with patch("api.authentication.firebase_authentication.auth") as mock_auth:
            mock_user = self._setup_auth_mocks(mock_auth)
            with patch("api.authentication.firebase_authentication.User") as MockUser:
                MockUser.objects.get.return_value = mock_user
                req = _auth_request(self.factory, "post", "/api/pets/mine/", payload={"name": "x"})
                resp = my_pets(req)
        self.assertEqual(resp.status_code, 405)

    # --- POST /api/pets/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_pet_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_pet.return_value = _make_pet(name="Luna")
            # Payload uses camelCase keys for multi-word fields
            payload = {"name": "Luna", "species": "cat", "isNfcSynced": False}
            req = _auth_request(self.factory, "post", "/api/pets/", payload)
            resp = pet_collection(req)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.content)["name"], "Luna")

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_pet_service_error(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_pet.side_effect = Exception("Validation error")
            payload = {"name": "Luna"}
            req = _auth_request(self.factory, "post", "/api/pets/", payload)
            resp = pet_collection(req)
        self.assertEqual(resp.status_code, 400)

    def test_pet_collection_method_not_allowed(self):
        with patch("api.authentication.firebase_authentication.auth") as mock_auth:
            mock_user = self._setup_auth_mocks(mock_auth)
            with patch("api.authentication.firebase_authentication.User") as MockUser:
                MockUser.objects.get.return_value = mock_user
                req = _auth_request(self.factory, "delete", "/api/pets/")
                resp = pet_collection(req)
        self.assertEqual(resp.status_code, 405)

    # --- GET /api/pets/<id>/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_get_pet_detail_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.get_pet.return_value = _make_pet()
            req = _auth_request(self.factory, "get", f"/api/pets/{PET_ID}/")
            resp = pet_detail(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["id"], PET_ID)

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_get_pet_detail_not_owner(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        mock_user.pets = []  # not owner
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            req = _auth_request(self.factory, "get", f"/api/pets/{PET_ID}/")
            resp = pet_detail(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 403)

    def test_get_pet_detail_no_auth(self):
        req = self.factory.get(f"/api/pets/{PET_ID}/")
        resp = pet_detail(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 401)

    # --- PUT /api/pets/<id>/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_update_pet_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.update_pet.return_value = _make_pet(name="Updated")
            payload = {"name": "Updated"}
            req = _auth_request(self.factory, "put", f"/api/pets/{PET_ID}/", payload)
            resp = pet_detail(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["name"], "Updated")

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_update_pet_service_error(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.update_pet.side_effect = Exception("Update failed")
            payload = {"name": "X"}
            req = _auth_request(self.factory, "put", f"/api/pets/{PET_ID}/", payload)
            resp = pet_detail(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 400)

    # --- DELETE /api/pets/<id>/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_delete_pet_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.delete_pet.return_value = None
            req = _auth_request(self.factory, "delete", f"/api/pets/{PET_ID}/")
            resp = pet_detail(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 204)

    def test_pet_detail_method_not_allowed(self):
        with patch("api.authentication.firebase_authentication.auth") as mock_auth:
            mock_user = self._setup_auth_mocks(mock_auth)
            with patch("api.authentication.firebase_authentication.User") as MockUser:
                MockUser.objects.get.return_value = mock_user
                req = _auth_request(self.factory, "patch", f"/api/pets/{PET_ID}/")
                resp = pet_detail(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 405)

    # --- POST /api/pets/<id>/vaccinations/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_add_vaccination_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.add_vaccination.return_value = _make_pet(vaccinations=[_make_vaccination()])
            # Payload uses camelCase keys (API input)
            payload = {
                "vaccineId": VACCINE_OBJ_ID,
                "dateGiven": "2026-01-15",
                "status": "completed",
            }
            req = _auth_request(self.factory, "post", f"/api/pets/{PET_ID}/vaccinations/", payload)
            resp = vaccinations(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 201)

    def test_vaccinations_method_not_allowed(self):
        with patch("api.authentication.firebase_authentication.auth") as mock_auth:
            mock_user = self._setup_auth_mocks(mock_auth)
            with patch("api.authentication.firebase_authentication.User") as MockUser:
                MockUser.objects.get.return_value = mock_user
                req = _auth_request(self.factory, "get", f"/api/pets/{PET_ID}/vaccinations/")
                resp = vaccinations(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 405)

    # --- POST /api/pets/<id>/vaccinations/<vid>/documents/ ---

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_add_document_to_vaccination_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.add_document_to_vaccination.return_value = _make_pet(
                vaccinations=[_make_vaccination(attached_documents=[_make_attached_doc()])]
            )
            # Payload uses camelCase keys (API input)
            payload = {
                "documentId": DOC_OBJ_ID,
                "fileName": "record.pdf",
                "fileUri": "https://storage.example.com/record.pdf",
            }
            req = _auth_request(self.factory, "post", f"/api/pets/{PET_ID}/vaccinations/{VACCINE_OBJ_ID}/documents/", payload)
            resp = vaccination_documents(req, pet_id=PET_ID, vaccination_id=VACCINE_OBJ_ID)
        self.assertEqual(resp.status_code, 201)

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_update_vaccination_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.update_vaccination.return_value = _make_pet(vaccinations=[_make_vaccination()])
            payload = {
                "vaccineId": VACCINE_OBJ_ID,
                "dateGiven": "2026-01-15",
                "status": "pending",
            }
            req = _auth_request(self.factory, "put", f"/api/pets/{PET_ID}/vaccinations/", payload)
            resp = vaccinations(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 200)

    @patch("api.views.pet_views.pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_delete_vaccination_ok(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.delete_vaccination.return_value = _make_pet(vaccinations=[])
            payload = {
                "vaccineId": VACCINE_OBJ_ID,
                "dateGiven": "2026-01-15",
            }
            req = _auth_request(self.factory, "delete", f"/api/pets/{PET_ID}/vaccinations/", payload)
            resp = vaccinations(req, pet_id=PET_ID)
        self.assertEqual(resp.status_code, 200)

    # --- Firebase invalid/expired token ---

    def test_pet_collection_invalid_token_returns_401(self):
        from firebase_admin import auth as real_auth
        with patch("api.authentication.firebase_authentication.auth") as mock_auth:
            mock_auth.RevokedIdTokenError = real_auth.RevokedIdTokenError
            mock_auth.ExpiredIdTokenError = real_auth.ExpiredIdTokenError
            mock_auth.InvalidIdTokenError = real_auth.InvalidIdTokenError
            mock_auth.verify_id_token.side_effect = real_auth.InvalidIdTokenError(
                "Invalid token", cause=None, http_response=None
            )
            req = _auth_request(self.factory, "get", "/api/pets/", token="bad_token")
            resp = pet_collection(req)
        self.assertEqual(resp.status_code, 401)


# ===========================================================================
# Serializer Tests
# ===========================================================================

class TestPetSerializer(TestCase):

    def test_pet_to_dict_basic(self):
        pet = _make_pet()
        result = pet_to_dict(pet)
        self.assertEqual(result["id"], PET_ID)
        self.assertEqual(result["name"], "Buddy")
        self.assertEqual(result["species"], "dog")
        self.assertEqual(result["breed"], "Labrador")
        self.assertEqual(result["gender"], "male")
        # camelCase output keys
        self.assertIn("birthDate", result)
        self.assertEqual(result["weight"], 25.50)
        self.assertEqual(result["color"], "golden")
        self.assertEqual(result["photoUrl"], "https://example.com/buddy.jpg")
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["isNfcSynced"])
        self.assertEqual(result["knownAllergies"], "")
        self.assertEqual(result["defaultVet"], "Dr. Smith")
        self.assertEqual(result["defaultClinic"], "Happy Paws")
        self.assertEqual(result["owners"], [USER_ID])

    def test_pet_to_dict_with_vaccinations(self):
        vacc = _make_vaccination()
        pet = _make_pet(vaccinations=[vacc])
        result = pet_to_dict(pet)
        self.assertEqual(len(result["vaccinations"]), 1)
        v = result["vaccinations"][0]
        # camelCase output keys for vaccination
        self.assertEqual(v["vaccineId"], VACCINE_OBJ_ID)
        self.assertEqual(v["status"], "completed")
        self.assertEqual(v["administeredBy"], "Dr. Smith")
        self.assertIn("dateGiven", v)
        self.assertIn("nextDueDate", v)
        self.assertIn("lotNumber", v)

    def test_pet_to_dict_with_attached_documents(self):
        doc = _make_attached_doc()
        vacc = _make_vaccination(attached_documents=[doc])
        pet = _make_pet(vaccinations=[vacc])
        result = pet_to_dict(pet)
        docs = result["vaccinations"][0]["attachedDocuments"]
        self.assertEqual(len(docs), 1)
        # camelCase output keys for documents
        self.assertEqual(docs[0]["documentId"], DOC_OBJ_ID)
        self.assertEqual(docs[0]["fileName"], "record.pdf")
        self.assertEqual(docs[0]["fileUri"], "https://storage.example.com/record.pdf")

    def test_pet_to_dict_none_weight(self):
        pet = _make_pet(weight=None)
        result = pet_to_dict(pet)
        self.assertIsNone(result["weight"])

    def test_pet_to_dict_empty_lists(self):
        pet = _make_pet(vaccinations=[])
        result = pet_to_dict(pet)
        self.assertEqual(result["vaccinations"], [])

    def test_format_date_with_date_object(self):
        d = date(2026, 3, 15)
        result = format_date(d)
        self.assertEqual(result, "2026-03-15")

    def test_format_date_with_datetime_object(self):
        dt = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = format_date(dt)
        self.assertIn("2026-03-15", result)

    def test_format_date_with_none(self):
        result = format_date(None)
        self.assertIsNone(result)

    def test_format_date_with_string(self):
        result = format_date("2026-03-15")
        self.assertEqual(result, "2026-03-15")
