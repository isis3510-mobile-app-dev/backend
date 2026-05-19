import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
from django.test import RequestFactory, TestCase
from django.utils import timezone

from api.models import EmergencyContact, LostPetReport, LostPetSighting, Pet, User
from api.serializers.lost_pet_serializer import (
    lost_pet_report_card_to_dict,
    lost_pet_report_detail_to_dict,
)
from api.services import lost_pet_service
from api.views.lost_pet_views import (
    pet_lost_report,
    public_lost_pet_collection,
)
from api.views.nfc_views import _approved_lost_contact


PET_ID = str(ObjectId())
USER_ID = str(ObjectId())
REPORT_ID = str(ObjectId())
SIGHTING_ID = str(ObjectId())


def _auth_request(factory, method, path, payload=None, token="valid_token"):
    body = json.dumps(payload) if payload else ""
    maker = getattr(factory, method)
    return maker(
        path,
        body,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _make_pet(**kwargs):
    pet = MagicMock(spec=Pet)
    pet.id = ObjectId(kwargs.get("id", PET_ID))
    pet.name = kwargs.get("name", "Milo")
    pet.species = kwargs.get("species", "cat")
    pet.breed = kwargs.get("breed", "Domestic Shorthair")
    pet.color = kwargs.get("color", "black")
    pet.photo_url = kwargs.get("photo_url", "https://example.com/milo.jpg")
    pet.status = kwargs.get("status", "lost")
    pet.known_allergies = kwargs.get("known_allergies", "Needs hypoallergenic food")
    return pet


def _make_report(**kwargs):
    report = MagicMock(spec=LostPetReport)
    report.id = ObjectId(kwargs.get("id", REPORT_ID))
    report.schema = kwargs.get("schema", 1)
    report.pet_id = ObjectId(kwargs.get("pet_id", PET_ID))
    report.owner_id = ObjectId(kwargs.get("owner_id", USER_ID))
    report.status = kwargs.get("status", "active")
    report.lost_note = kwargs.get("lost_note", "Very shy, do not chase.")
    report.last_seen_location = kwargs.get("last_seen_location", "Central Park")
    report.last_seen_latitude = kwargs.get("last_seen_latitude", 4.65)
    report.last_seen_longitude = kwargs.get("last_seen_longitude", -74.08)
    report.last_seen_at = kwargs.get("last_seen_at", datetime(2026, 5, 1, 12, 0))
    report.expose_medical_info = kwargs.get("expose_medical_info", False)
    report.emergency_contacts = kwargs.get("emergency_contacts", [])
    report.created_at = kwargs.get("created_at", datetime(2026, 5, 1, 13, 0))
    report.updated_at = kwargs.get("updated_at", datetime(2026, 5, 1, 13, 30))
    report.resolved_at = kwargs.get("resolved_at", None)
    return report


def _make_sighting(**kwargs):
    sighting = MagicMock(spec=LostPetSighting)
    sighting.id = ObjectId(kwargs.get("id", SIGHTING_ID))
    sighting.schema = kwargs.get("schema", 1)
    sighting.report_id = ObjectId(kwargs.get("report_id", REPORT_ID))
    sighting.pet_id = ObjectId(kwargs.get("pet_id", PET_ID))
    sighting.seen_at = kwargs.get("seen_at", datetime(2026, 5, 2, 9, 30))
    sighting.location = kwargs.get("location", "Library entrance")
    sighting.latitude = kwargs.get("latitude", 4.66)
    sighting.longitude = kwargs.get("longitude", -74.09)
    sighting.note = kwargs.get("note", "Cat was walking east.")
    sighting.photo_url = kwargs.get("photo_url", None)
    sighting.reporter_name = kwargs.get("reporter_name", "Ana")
    sighting.reporter_phone = kwargs.get("reporter_phone", "+571234567")
    sighting.reporter_email = kwargs.get("reporter_email", "ana@example.com")
    sighting.created_at = kwargs.get("created_at", datetime(2026, 5, 2, 9, 40))
    return sighting


class TestLostPetSerializers(TestCase):
    def test_public_card_exposes_only_owner_approved_contact_channels(self):
        report = _make_report(
            emergency_contacts=[
                {
                    "name": "Owner",
                    "phone": "+571111111",
                    "whatsapp": "+572222222",
                    "expose_phone": True,
                    "expose_whatsapp": True,
                },
                {
                    "name": "Hidden",
                    "phone": "+573333333",
                    "whatsapp": "+574444444",
                    "expose_phone": False,
                    "expose_whatsapp": False,
                }
            ]
        )
        data = lost_pet_report_card_to_dict(report, _make_pet())

        self.assertEqual(data["pet"]["name"], "Milo")
        self.assertEqual(len(data["emergencyContacts"]), 1)
        self.assertEqual(data["emergencyContacts"][0]["phone"], "+571111111")
        self.assertEqual(data["emergencyContacts"][0]["whatsapp"], "+572222222")
        self.assertNotIn("lostNote", data)
        self.assertNotIn("knownAllergies", data)

    def test_public_detail_exposes_only_allowed_contact_channels(self):
        report = _make_report(
            expose_medical_info=True,
            emergency_contacts=[
                {
                    "name": "Primary",
                    "phone": "+571111111",
                    "whatsapp": "+572222222",
                    "expose_phone": True,
                    "expose_whatsapp": False,
                },
                {
                    "name": "Hidden",
                    "phone": "+573333333",
                    "whatsapp": "+574444444",
                    "expose_phone": False,
                    "expose_whatsapp": False,
                },
            ]
        )

        data = lost_pet_report_detail_to_dict(report, _make_pet())

        self.assertEqual(data["lostNote"], "Very shy, do not chase.")
        self.assertEqual(data["knownAllergies"], "Needs hypoallergenic food")
        self.assertTrue(data["exposeMedicalInfo"])
        self.assertEqual(len(data["emergencyContacts"]), 1)
        self.assertEqual(data["emergencyContacts"][0]["phone"], "+571111111")
        self.assertEqual(data["emergencyContacts"][0]["whatsapp"], "")
        self.assertNotIn("+573333333", json.dumps(data))

    def test_nfc_public_contact_skips_contacts_without_exposed_channels(self):
        report = _make_report(
            emergency_contacts=[
                {
                    "name": "Hidden",
                    "phone": "+573333333",
                    "whatsapp": "+574444444",
                    "expose_phone": False,
                    "expose_whatsapp": False,
                },
                {
                    "name": "Visible",
                    "phone": "+571111111",
                    "whatsapp": "+572222222",
                    "expose_phone": False,
                    "expose_whatsapp": True,
                },
            ]
        )

        data = _approved_lost_contact(report)

        self.assertEqual(data["ownerName"], "Visible")
        self.assertEqual(data["ownerPhone"], "")
        self.assertEqual(data["ownerWhatsapp"], "+572222222")


class TestLostPetService(TestCase):
    def test_report_payload_converts_contacts_and_datetimes_for_mongo(self):
        payload = lost_pet_service._report_payload({
            "lastSeenAt": "2026-05-18T10:14:35.237519",
            "emergencyContacts": [
                {
                    "name": "Carlos Mendez",
                    "phone": "+573012345678",
                    "whatsapp": "+573012345678",
                    "exposePhone": True,
                    "exposeWhatsapp": True,
                    "preferred": True,
                }
            ],
        })

        self.assertTrue(timezone.is_aware(payload["last_seen_at"]))
        self.assertIsInstance(payload["emergency_contacts"][0], dict)
        self.assertTrue(payload["emergency_contacts"][0]["expose_phone"])

    @patch("api.services.lost_pet_service.LostPetReport")
    @patch("api.services.lost_pet_service.User")
    @patch("api.services.lost_pet_service.Pet")
    def test_backfill_creates_report_for_lost_pet_with_owner_contact(self, MockPet, MockUser, MockReport):
        pet = _make_pet(status="lost")
        pet.owners = [ObjectId(USER_ID)]
        owner = MagicMock(spec=User)
        owner.id = ObjectId(USER_ID)
        owner.name = "Carlos Mendez"
        owner.phone = "+573001234567"
        report = _make_report(pet_id=PET_ID, owner_id=USER_ID, lost_note="")

        MockPet.objects.filter.return_value.only.return_value = [pet]
        MockReport.objects.filter.return_value = []
        MockReport.objects.create.return_value = report
        MockReport.objects.get.return_value = report
        MockUser.objects.get.return_value = owner

        results = lost_pet_service.backfill_lost_reports_for_lost_pets(commit=True)

        self.assertEqual(results[0]["action"], "created_report")
        _, kwargs = MockReport.objects.create.call_args
        self.assertEqual(kwargs["lost_note"], "")
        self.assertEqual(kwargs["status"], "active")
        self.assertTrue(kwargs["last_seen_location"].endswith("Bogotá"))
        self.assertFalse(kwargs["expose_medical_info"])
        self.assertEqual(kwargs["emergency_contacts"][0]["name"], "Carlos Mendez")
        self.assertEqual(kwargs["emergency_contacts"][0]["phone"], "+573001234567")
        self.assertFalse(kwargs["emergency_contacts"][0]["expose_phone"])

    @patch("api.services.notification_service.create_notification")
    @patch("api.services.lost_pet_service.LostPetSighting")
    @patch("api.services.lost_pet_service.Pet")
    @patch("api.services.lost_pet_service.LostPetReport")
    def test_create_sighting_updates_report_last_seen(self, MockReport, MockPet, MockSighting, mock_notify):
        report = _make_report()
        updated_report = _make_report(last_seen_location="Library entrance")
        pet = _make_pet()
        sighting = _make_sighting()

        MockReport.objects.get.side_effect = [report, updated_report]
        MockPet.objects.only.return_value.get.return_value = pet
        MockSighting.objects.create.return_value = sighting
        MockSighting.objects.get.return_value = sighting

        payload = {
            "seenAt": "2026-05-02T09:30:00Z",
            "location": "Library entrance",
            "latitude": 4.66,
            "longitude": -74.09,
            "note": "Cat was walking east.",
        }

        result, _, _ = lost_pet_service.create_sighting(REPORT_ID, payload)

        self.assertEqual(result, sighting)
        self.assertEqual(report.last_seen_location, "Library entrance")
        self.assertEqual(report.last_seen_latitude, 4.66)
        self.assertEqual(report.last_seen_longitude, -74.09)
        self.assertIsNotNone(report.last_seen_at)
        report.save.assert_called_once()
        mock_notify.assert_called_once()
        notification_payload = mock_notify.call_args.args[0]
        self.assertEqual(notification_payload["actionPetName"], "Milo")
        self.assertEqual(notification_payload["actionPetPhotoUrl"], "https://example.com/milo.jpg")
        self.assertEqual(notification_payload["actionReporterName"], "Ana")

    @patch("api.services.lost_pet_service.LostPetReport")
    @patch("api.services.lost_pet_service.Pet")
    def test_create_or_reactivate_report_creates_new_episode_after_resolved_report(self, MockPet, MockReport):
        pet = _make_pet(status="healthy")
        updated_pet = _make_pet(status="lost")
        resolved_report = _make_report(status="resolved")
        new_report = _make_report(status="active")
        MockPet.objects.get.side_effect = [pet, updated_pet]
        MockReport.objects.filter.return_value = [resolved_report]
        MockReport.objects.create.return_value = new_report
        MockReport.objects.get.return_value = new_report

        result, updated_pet = lost_pet_service.create_or_reactivate_report(
            PET_ID,
            USER_ID,
            {"lostNote": "Last seen near home."},
        )

        self.assertEqual(result, new_report)
        self.assertEqual(updated_pet.status, "lost")
        resolved_report.save.assert_not_called()
        MockReport.objects.create.assert_called_once()
        pet.save.assert_not_called()
        MockPet.objects.filter.assert_called_once_with(id=ObjectId(PET_ID))
        MockPet.objects.filter.return_value.update.assert_called_once_with(status="lost")

    @patch("api.services.lost_pet_service.LostPetReport")
    @patch("api.services.lost_pet_service.Pet")
    def test_create_report_creates_new_episode_when_pet_was_found_even_with_stale_active_report(self, MockPet, MockReport):
        pet = _make_pet(status="healthy")
        updated_pet = _make_pet(status="lost")
        stale_active_report = _make_report(status="active")
        new_report = _make_report(status="active")
        MockPet.objects.get.side_effect = [pet, updated_pet]
        MockReport.objects.filter.return_value = [stale_active_report]
        MockReport.objects.create.return_value = new_report
        MockReport.objects.get.return_value = new_report

        result, updated_pet = lost_pet_service.create_or_reactivate_report(
            PET_ID,
            USER_ID,
            {"lostNote": "Lost again."},
        )

        self.assertEqual(result, new_report)
        self.assertEqual(updated_pet.status, "lost")
        self.assertEqual(stale_active_report.status, "resolved")
        stale_active_report.save.assert_called_once()
        MockReport.objects.create.assert_called_once()
        MockPet.objects.filter.return_value.update.assert_called_once_with(status="lost")

    @patch("api.services.lost_pet_service.LostPetReport")
    @patch("api.services.lost_pet_service.Pet")
    def test_mark_pet_found_normalizes_embedded_contacts_before_save(self, MockPet, MockReport):
        pet = _make_pet(status="lost")
        report = _make_report(
            emergency_contacts=[
                EmergencyContact(
                    name="Owner",
                    phone="+571111111",
                    whatsapp="+571111111",
                    expose_phone=True,
                    expose_whatsapp=True,
                    preferred=True,
                )
            ]
        )
        MockPet.objects.get.side_effect = [pet, pet]
        MockReport.objects.filter.return_value = [report]

        lost_pet_service.mark_pet_found(PET_ID)

        self.assertEqual(report.status, "resolved")
        self.assertIsInstance(report.emergency_contacts[0], dict)
        self.assertEqual(report.emergency_contacts[0]["phone"], "+571111111")
        report.save.assert_called_once()
        pet.save.assert_not_called()
        MockPet.objects.filter.assert_called_once_with(id=ObjectId(PET_ID))
        MockPet.objects.filter.return_value.update.assert_called_once_with(status="healthy")

    @patch("api.services.lost_pet_service.LostPetReport")
    @patch("api.services.lost_pet_service.Pet")
    def test_update_report_creates_new_episode_when_latest_report_is_resolved(self, MockPet, MockReport):
        report = _make_report(status="resolved")
        new_report = _make_report(status="active")
        fresh_pet = _make_pet(status="lost")
        MockReport.objects.filter.return_value = [report]
        MockReport.objects.create.return_value = new_report
        MockReport.objects.get.return_value = new_report
        MockPet.objects.get.return_value = fresh_pet

        result, pet = lost_pet_service.update_report_for_pet(PET_ID, {"lostNote": "Still missing."})

        self.assertEqual(result, new_report)
        self.assertEqual(pet.status, "lost")
        report.save.assert_not_called()
        MockReport.objects.create.assert_called_once()
        MockPet.objects.filter.assert_called_once_with(id=ObjectId(PET_ID))
        MockPet.objects.filter.return_value.update.assert_called_once_with(status="lost")


class TestLostPetViews(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _setup_auth_mocks(self, mock_auth, owns_pet=True):
        mock_user = MagicMock(spec=User)
        mock_user.id = ObjectId(USER_ID)
        mock_user.firebase_uid = "uid123"
        mock_user.pets = [ObjectId(PET_ID)] if owns_pet else []
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}
        return mock_user

    @patch("api.views.lost_pet_views.lost_pet_service")
    def test_public_lost_pet_list_requires_no_auth_and_only_safe_contact_data(self, mock_svc):
        mock_svc.list_active_reports_with_pets.return_value = [(_make_report(), _make_pet())]
        req = self.factory.get("/api/lost-pets/")

        resp = public_lost_pet_collection(req)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn("emergencyContacts", data[0])
        self.assertNotIn("knownAllergies", data[0])

    @patch("api.views.lost_pet_views.lost_pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_owner_lost_report_rejects_non_owner(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth, owns_pet=False)
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            req = _auth_request(self.factory, "get", f"/api/pets/{PET_ID}/lost-report/")
            resp = pet_lost_report(req, pet_id=PET_ID)

        self.assertEqual(resp.status_code, 403)
        mock_svc.get_report_for_pet.assert_not_called()

    @patch("api.views.lost_pet_views.lost_pet_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_owner_can_create_lost_report(self, mock_auth, mock_svc):
        mock_user = self._setup_auth_mocks(mock_auth, owns_pet=True)
        mock_svc.create_or_reactivate_report.return_value = (_make_report(), _make_pet(status="lost"))

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            req = _auth_request(
                self.factory,
                "post",
                f"/api/pets/{PET_ID}/lost-report/",
                payload={"lostNote": "Last seen near home."},
            )
            resp = pet_lost_report(req, pet_id=PET_ID)

        self.assertEqual(resp.status_code, 201)
        mock_svc.create_or_reactivate_report.assert_called_once_with(
            PET_ID,
            mock_user.id,
            {"lostNote": "Last seen near home."},
        )
