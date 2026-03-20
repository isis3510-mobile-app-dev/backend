import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from bson import ObjectId
from datetime import datetime

from api.models import Notification, User
from api.services import notification_service
from api.views.notification_views import notification_collection, notification_detail
from api.serializers.notification_serializer import notification_to_dict

USER_ID = str(ObjectId())
NOTIF_ID = str(ObjectId())


def _auth_request(factory, method, path, payload=None, token="valid_token"):
    body = json.dumps(payload) if payload else ""
    maker = getattr(factory, method)
    return maker(
        path,
        body,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _make_notification(**kwargs):
    n = MagicMock(spec=Notification)
    n.id = ObjectId(kwargs.get("id", NOTIF_ID))
    n.schema = kwargs.get("schema", 1)
    n.user_id = kwargs.get("user_id", USER_ID)
    n.type = kwargs.get("type", "alert")
    n.header = kwargs.get("header", "Vaccine Due")
    n.text = kwargs.get("text", "Buddy needs a vaccine.")
    n.date_sent = kwargs.get("date_sent", datetime(2026, 3, 10))
    n.date_clicked = kwargs.get("date_clicked", None)
    n.is_read = kwargs.get("is_read", False)
    n.is_dismissed = kwargs.get("is_dismissed", False)
    n.date_dismissed = kwargs.get("date_dismissed", None)
    return n


class TestNotificationService(TestCase):

    @patch("api.services.notification_service.Notification")
    def test_create_notification(self, MockNotif):
        created = MagicMock()
        created.header = "New Notif"
        MockNotif.objects.create.return_value = created
        MockNotif.objects.get.return_value = created

        # API sends camelCase; service must translate before ORM
        data = {"header": "New Notif", "userId": USER_ID}
        result = notification_service.create_notification(data)
        self.assertEqual(result.header, "New Notif")

    @patch("api.services.notification_service.Notification")
    def test_update_notification_translates_dismiss_fields(self, MockNotif):
        notif = _make_notification()
        MockNotif.objects.get.return_value = notif

        payload = {
            "isDismissed": True,
            "dateDismissed": "2026-03-20T12:00:00Z",
        }
        result = notification_service.update_notification(NOTIF_ID, payload)

        self.assertTrue(result.is_dismissed)
        self.assertIsNotNone(result.date_dismissed)


class TestNotificationViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch("api.views.notification_views.notification_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_list_notifications_ok(self, mock_auth, mock_svc):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.list_notifications.return_value = [_make_notification()]
            req = _auth_request(self.factory, "get", f"/api/notifications/?user_id={USER_ID}")
            resp = notification_collection(req)

        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data[0]["header"], "Vaccine Due")

    @patch("api.views.notification_views.notification_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_notification_ok(self, mock_auth, mock_svc):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_notification.return_value = _make_notification()
            # Payload uses camelCase keys
            payload = {
                "userId": USER_ID,
                "type": "alert",
                "header": "Vaccine Due",
                "text": "Buddy needs a vaccine.",
            }
            req = _auth_request(self.factory, "post", "/api/notifications/", payload)
            resp = notification_collection(req)

        self.assertEqual(resp.status_code, 201)


class TestNotificationSerializer(TestCase):

    def test_notification_to_dict(self):
        notif = _make_notification()
        result = notification_to_dict(notif)
        # Response JSON uses camelCase
        self.assertEqual(result["header"], "Vaccine Due")
        self.assertEqual(result["userId"], USER_ID)
        self.assertIn("dateSent", result)
        self.assertIn("dateClicked", result)
        self.assertIn("isRead", result)
        self.assertIn("isDismissed", result)
        self.assertIn("dateDismissed", result)
        self.assertFalse(result["isRead"])
        self.assertFalse(result["isDismissed"])
