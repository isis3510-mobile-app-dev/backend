import json
from unittest.mock import MagicMock, patch
from datetime import datetime

from bson import ObjectId
from django.test import RequestFactory, TestCase

from api.models import Medicine, User
from api.serializers.medicine_serializer import medicine_to_dict
from api.services import medicine_service
from api.views.medicine_views import medicine_collection


PET_ID = str(ObjectId())
OWNER_ID = str(ObjectId())
MEDICINE_ID = str(ObjectId())


def _auth_request(factory, method, path, payload=None, token="valid_token"):
    body = json.dumps(payload) if payload else ""
    maker = getattr(factory, method)
    return maker(
        path,
        body,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _make_medicine(**kwargs):
    medicine = MagicMock(spec=Medicine)
    medicine.id = ObjectId(kwargs.get("id", MEDICINE_ID))
    medicine.schema = kwargs.get("schema", 1)
    medicine.pet_id = kwargs.get("pet_id", PET_ID)
    medicine.owner_id = kwargs.get("owner_id", OWNER_ID)
    medicine.medicine_name = kwargs.get("medicine_name", "Amoxicillin")
    medicine.administration_route = kwargs.get("administration_route", "oral")
    medicine.dosage_value = kwargs.get("dosage_value", 5.0)
    medicine.dosage_unit = kwargs.get("dosage_unit", "mg")
    medicine.frequency = kwargs.get("frequency", 12)
    medicine.start_date = kwargs.get("start_date", datetime(2026, 3, 15, 8, 0))
    medicine.end_date = kwargs.get("end_date", datetime(2026, 3, 22, 8, 0))
    medicine.photo_url = kwargs.get("photo_url", "https://example.com/medicine.jpg")
    medicine.reminder_enabled = kwargs.get("reminder_enabled", True)
    medicine.last_administered = kwargs.get("last_administered", None)
    return medicine


class TestMedicineService(TestCase):

    @patch("api.services.medicine_service.Medicine")
    @patch("api.services.medicine_service.Pet")
    def test_create_medicine(self, MockPet, MockMedicine):
        mock_user = MagicMock()
        mock_user.id = OWNER_ID
        mock_user.pets = [PET_ID]

        MockPet.objects.get.return_value = MagicMock(id=ObjectId(PET_ID))
        created = _make_medicine()
        MockMedicine.objects.create.return_value = created
        MockMedicine.objects.get.return_value = created

        payload = {
            "petId": PET_ID,
            "medicineName": "Amoxicillin",
            "administrationRoute": "oral",
            "dosageValue": 5.0,
            "dosageUnit": "mg",
            "frequency": 12,
            "startDate": "2026-03-15T08:00:00Z",
            "endDate": "2026-03-22T08:00:00Z",
            "reminderEnabled": True,
        }

        result = medicine_service.create_medicine(mock_user, payload)

        self.assertEqual(result.medicine_name, "Amoxicillin")
        MockMedicine.objects.create.assert_called_once()

    @patch("api.services.medicine_service.Medicine")
    def test_list_medicines_for_pet(self, MockMedicine):
        MockMedicine.objects.filter.return_value = [_make_medicine()]
        result = medicine_service.list_medicines_for_pet(PET_ID)
        self.assertEqual(len(result), 1)


class TestMedicineViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch("api.views.medicine_views.medicine_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_medicine_ok(self, mock_auth, mock_svc):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_user.pets = [PET_ID]
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_medicine.return_value = _make_medicine()
            payload = {
                "petId": PET_ID,
                "medicineName": "Amoxicillin",
                "administrationRoute": "oral",
                "dosageValue": 5.0,
                "dosageUnit": "mg",
                "frequency": 12,
                "startDate": "2026-03-15T08:00:00Z",
                "endDate": "2026-03-22T08:00:00Z",
                "reminderEnabled": True,
            }
            req = _auth_request(self.factory, "post", f"/api/medicines/", payload)
            resp = medicine_collection(req)

        self.assertEqual(resp.status_code, 201)

    @patch("api.views.medicine_views.medicine_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_list_medicines_ok(self, mock_auth, mock_svc):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_user.pets = [PET_ID]
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.list_medicines.return_value = [_make_medicine()]
            req = _auth_request(self.factory, "get", f"/api/medicines/?pet_id={PET_ID}")
            resp = medicine_collection(req)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data[0]["medicineName"], "Amoxicillin")


class TestMedicineSerializer(TestCase):

    def test_medicine_to_dict(self):
        medicine = _make_medicine()
        result = medicine_to_dict(medicine) or {}
        self.assertEqual(result["medicineName"], "Amoxicillin")
        self.assertEqual(result["petId"], PET_ID)
        self.assertEqual(result["administrationRoute"], "oral")
        self.assertEqual(result["photoUrl"], "https://example.com/medicine.jpg")
        self.assertIn("startDate", result)
        self.assertIn("lastAdministered", result)
