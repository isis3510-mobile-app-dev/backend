import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from bson import ObjectId
from datetime import datetime

from api.models import Event, User
from api.services import event_service
from api.views.event_views import event_collection, event_detail, event_documents
from api.serializers.event_serializer import event_to_dict

PET_ID = str(ObjectId())
OWNER_ID = str(ObjectId())
EVENT_ID = str(ObjectId())
DOC_OBJ_ID = str(ObjectId())


def _auth_request(factory, method, path, payload=None, token="valid_token"):
    body = json.dumps(payload) if payload else ""
    maker = getattr(factory, method)
    return maker(
        path,
        body,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _make_event(**kwargs):
    e = MagicMock(spec=Event)
    e.id = ObjectId(kwargs.get("id", EVENT_ID))
    e.schema = kwargs.get("schema", 1)
    e.pet_id = kwargs.get("pet_id", PET_ID)
    e.owner_id = kwargs.get("owner_id", OWNER_ID)
    e.title = kwargs.get("title", "Checkup")
    e.event_type = kwargs.get("event_type", "medical")
    e.date = kwargs.get("date", datetime(2026, 3, 15))
    e.price = kwargs.get("price", 50.0)
    e.provider = kwargs.get("provider", "Dr. Smith")
    e.clinic = kwargs.get("clinic", "Happy Paws")
    e.description = kwargs.get("description", "Regular checkup")
    e.follow_up_date = kwargs.get("follow_up_date", None)
    e.attached_documents = kwargs.get("attached_documents", [])
    return e


class TestEventService(TestCase):

    @patch("api.services.event_service.Event")
    def test_create_event(self, MockEvent):
        created = MagicMock()
        created.title = "New Event"
        MockEvent.objects.create.return_value = created
        MockEvent.objects.get.return_value = created

        # API sends camelCase; service must translate before ORM
        data = {"title": "New Event", "petId": PET_ID, "ownerId": OWNER_ID}
        result = event_service.create_event(data)
        self.assertEqual(result.title, "New Event")

    @patch("api.services.event_service.Event")
    def test_list_events(self, MockEvent):
        MockEvent.objects.filter.return_value = [_make_event()]
        result = event_service.list_events(filters={"pet_id": PET_ID})
        self.assertEqual(len(result), 1)


class TestEventViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch("api.views.event_views.event_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_list_events_ok(self, mock_auth, mock_svc):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.list_events.return_value = [_make_event()]
            req = _auth_request(self.factory, "get", f"/api/events/?pet_id={PET_ID}")
            resp = event_collection(req)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data[0]["title"], "Checkup")

    @patch("api.views.event_views.event_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_event_ok(self, mock_auth, mock_svc):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_event.return_value = _make_event()
            # Payload uses camelCase keys
            payload = {
                "petId": PET_ID,
                "ownerId": OWNER_ID,
                "title": "Checkup",
                "eventType": "medical",
                "date": "2026-03-15T00:00:00Z",
            }
            req = _auth_request(self.factory, "post", "/api/events/", payload)
            resp = event_collection(req)

        self.assertEqual(resp.status_code, 201)


class TestEventSerializer(TestCase):

    def test_event_to_dict(self):
        event = _make_event()
        result = event_to_dict(event)
        # Response JSON uses camelCase
        self.assertEqual(result["title"], "Checkup")
        self.assertEqual(result["petId"], PET_ID)
        self.assertEqual(result["ownerId"], OWNER_ID)
        self.assertEqual(result["eventType"], "medical")
        self.assertIn("followUpDate", result)
        self.assertIn("attachedDocuments", result)
