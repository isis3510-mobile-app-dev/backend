import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from bson import ObjectId

from api.views.screen_views import screen_collection, screen_detail
from api.views.screen_time_log_views import screen_time_log_collection
from api.models import Screen, ScreenTimeLog
from api.services import screen_service, screen_time_log_service
from api.serializers.screen_serializer import screen_to_dict
from api.serializers.screen_time_log_serializer import screen_time_log_to_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCREEN_ID = str(ObjectId())
USER_ID   = str(ObjectId())

def _make_screen(**kwargs):
    s = MagicMock(spec=Screen)
    s.id          = ObjectId(SCREEN_ID)
    s.schema      = kwargs.get("schema", 1)
    s.name        = kwargs.get("name", "HomeScreen")
    s.hasAds      = kwargs.get("hasAds", False)
    s.appType     = kwargs.get("appType", "Kotlin")
    s.buttons     = kwargs.get("buttons", [])
    return s

def _make_log(**kwargs):
    from datetime import datetime, timezone
    log = MagicMock(spec=ScreenTimeLog)
    log.id        = ObjectId()
    log.schema    = 1
    log.userId    = kwargs.get("userId", USER_ID)
    log.screenId  = kwargs.get("screenId", SCREEN_ID)
    log.startTime = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    log.endTime   = datetime(2026, 3, 15, 10, 2, 30, tzinfo=timezone.utc)
    log.totalTime = kwargs.get("totalTime", 150)
    log.appType   = kwargs.get("appType", "Kotlin")
    return log


# ===========================================================================
# Screen Service Tests
# ===========================================================================

class TestScreenService(TestCase):

    @patch("api.services.screen_service.Screen")
    def test_list_screens_returns_all(self, MockScreen):
        mock_qs = [_make_screen(name="A"), _make_screen(name="B")]
        MockScreen.objects.all.return_value = mock_qs
        result = screen_service.list_screens()
        self.assertEqual(result, mock_qs)
        MockScreen.objects.all.assert_called_once()

    @patch("api.services.screen_service.Screen")
    def test_get_screen_found(self, MockScreen):
        expected = _make_screen()
        MockScreen.objects.get.return_value = expected
        result = screen_service.get_screen(SCREEN_ID)
        self.assertEqual(result, expected)
        MockScreen.objects.get.assert_called_once_with(id=SCREEN_ID)

    @patch("api.services.screen_service.Screen")
    def test_get_screen_not_found_raises(self, MockScreen):
        MockScreen.DoesNotExist = Screen.DoesNotExist
        MockScreen.objects.get.side_effect = Screen.DoesNotExist
        with self.assertRaises(Screen.DoesNotExist):
            screen_service.get_screen("nonexistent_id")

    @patch("api.services.screen_service.Screen")
    def test_create_screen(self, MockScreen):
        created = _make_screen(name="NewScreen")
        MockScreen.objects.create.return_value = created
        MockScreen.objects.get.return_value = created
        result = screen_service.create_screen({"name": "NewScreen", "hasAds": False})
        self.assertEqual(result.name, "NewScreen")
        MockScreen.objects.create.assert_called_once()

    @patch("api.services.screen_service.Screen")
    def test_update_screen(self, MockScreen):
        screen = _make_screen(name="OldName")
        updated = _make_screen(name="NewName")
        MockScreen.objects.get.side_effect = [screen, updated]
        result = screen_service.update_screen(SCREEN_ID, {"name": "NewName"})
        screen.save.assert_called_once()
        self.assertEqual(result.name, "NewName")

    @patch("api.services.screen_service.Screen")
    def test_delete_screen(self, MockScreen):
        MockScreen.objects.filter.return_value.delete.return_value = None
        screen_service.delete_screen(SCREEN_ID)
        MockScreen.objects.filter.assert_called_once_with(id=SCREEN_ID)
        MockScreen.objects.filter.return_value.delete.assert_called_once()


# ===========================================================================
# Screen View Tests
# ===========================================================================

class TestScreenViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # --- GET /api/screens/ ---

    @patch("api.views.screen_views.screen_service")
    def test_list_screens_ok(self, mock_svc):
        mock_svc.list_screens.return_value = [_make_screen(name="Home")]
        req = self.factory.get("/api/screens/")
        resp = screen_collection(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["name"], "Home")

    @patch("api.views.screen_views.screen_service")
    def test_list_screens_empty(self, mock_svc):
        mock_svc.list_screens.return_value = []
        req = self.factory.get("/api/screens/")
        resp = screen_collection(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), [])

    @patch("api.views.screen_views.screen_service")
    def test_list_screens_service_error(self, mock_svc):
        mock_svc.list_screens.side_effect = Exception("DB error")
        req = self.factory.get("/api/screens/")
        resp = screen_collection(req)
        self.assertEqual(resp.status_code, 500)
        self.assertIn("error", json.loads(resp.content))

    # --- POST /api/screens/ ---

    @patch("api.views.screen_views.screen_service")
    def test_create_screen_ok(self, mock_svc):
        mock_svc.create_screen.return_value = _make_screen(name="LoginScreen")
        payload = {"name": "LoginScreen", "hasAds": False, "buttons": []}
        req = self.factory.post(
            "/api/screens/", json.dumps(payload), content_type="application/json"
        )
        resp = screen_collection(req)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.content)["name"], "LoginScreen")

    @patch("api.views.screen_views.screen_service")
    def test_create_screen_invalid_json(self, mock_svc):
        req = self.factory.post(
            "/api/screens/", "not-json", content_type="application/json"
        )
        resp = screen_collection(req)
        self.assertEqual(resp.status_code, 400)

    @patch("api.views.screen_views.screen_service")
    def test_create_screen_service_error(self, mock_svc):
        mock_svc.create_screen.side_effect = Exception("Validation error")
        payload = {"name": "X"}
        req = self.factory.post(
            "/api/screens/", json.dumps(payload), content_type="application/json"
        )
        resp = screen_collection(req)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", json.loads(resp.content))

    # --- Method not allowed on collection ---

    def test_screen_collection_method_not_allowed(self):
        req = self.factory.delete("/api/screens/")
        resp = screen_collection(req)
        self.assertEqual(resp.status_code, 405)

    # --- GET /api/screens/<id>/ ---

    @patch("api.views.screen_views.screen_service")
    def test_get_screen_detail_ok(self, mock_svc):
        mock_svc.get_screen.return_value = _make_screen()
        req = self.factory.get(f"/api/screens/{SCREEN_ID}/")
        resp = screen_detail(req, screen_id=SCREEN_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["id"], SCREEN_ID)

    @patch("api.views.screen_views.screen_service")
    def test_get_screen_detail_not_found(self, mock_svc):
        mock_svc.get_screen.side_effect = Screen.DoesNotExist
        req = self.factory.get(f"/api/screens/badid/")
        resp = screen_detail(req, screen_id="badid")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Screen not found", json.loads(resp.content)["error"])

    # --- PUT /api/screens/<id>/ ---

    @patch("api.views.screen_views.screen_service")
    def test_update_screen_ok(self, mock_svc):
        mock_svc.update_screen.return_value = _make_screen(name="Updated")
        payload = {"name": "Updated"}
        req = self.factory.put(
            f"/api/screens/{SCREEN_ID}/", json.dumps(payload), content_type="application/json"
        )
        resp = screen_detail(req, screen_id=SCREEN_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["name"], "Updated")

    @patch("api.views.screen_views.screen_service")
    def test_update_screen_not_found(self, mock_svc):
        mock_svc.update_screen.side_effect = Screen.DoesNotExist
        req = self.factory.put(
            "/api/screens/badid/", json.dumps({"name": "X"}), content_type="application/json"
        )
        resp = screen_detail(req, screen_id="badid")
        self.assertEqual(resp.status_code, 404)

    # --- DELETE /api/screens/<id>/ ---

    @patch("api.views.screen_views.screen_service")
    def test_delete_screen_ok(self, mock_svc):
        mock_svc.delete_screen.return_value = None
        req = self.factory.delete(f"/api/screens/{SCREEN_ID}/")
        resp = screen_detail(req, screen_id=SCREEN_ID)
        self.assertEqual(resp.status_code, 204)

    @patch("api.views.screen_views.screen_service")
    def test_delete_screen_not_found(self, mock_svc):
        mock_svc.delete_screen.side_effect = Screen.DoesNotExist
        req = self.factory.delete("/api/screens/badid/")
        resp = screen_detail(req, screen_id="badid")
        self.assertEqual(resp.status_code, 404)

    # --- Method not allowed on detail ---

    def test_screen_detail_method_not_allowed(self):
        req = self.factory.patch(f"/api/screens/{SCREEN_ID}/")
        resp = screen_detail(req, screen_id=SCREEN_ID)
        self.assertEqual(resp.status_code, 405)


# ===========================================================================
# ScreenTimeLog Service Tests
# ===========================================================================

class TestScreenTimeLogService(TestCase):

    @patch("api.services.screen_time_log_service.ScreenTimeLog")
    def test_list_logs_no_filter(self, MockLog):
        MockLog.objects.all.return_value = []
        result = screen_time_log_service.list_logs()
        self.assertEqual(result, [])

    @patch("api.services.screen_time_log_service.ScreenTimeLog")
    def test_list_logs_filter_user(self, MockLog):
        qs = MagicMock()
        MockLog.objects.all.return_value = qs
        qs.filter.return_value = qs
        screen_time_log_service.list_logs(user_id=USER_ID)
        qs.filter.assert_called_with(userId=USER_ID)

    @patch("api.services.screen_time_log_service.ScreenTimeLog")
    def test_list_logs_filter_screen(self, MockLog):
        qs = MagicMock()
        MockLog.objects.all.return_value = qs
        qs.filter.return_value = qs
        screen_time_log_service.list_logs(screen_id=SCREEN_ID)
        qs.filter.assert_called_with(screenId=SCREEN_ID)

    @patch("api.services.screen_time_log_service.ScreenTimeLog")
    def test_create_log_auto_total_time(self, MockLog):
        created = _make_log(totalTime=150)
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "screenId": SCREEN_ID,
            "startTime": "2026-03-15T10:00:00",
            "endTime":   "2026-03-15T10:02:30",
        }
        log = screen_time_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        self.assertEqual(call_kwargs["totalTime"], 150)

    @patch("api.services.screen_time_log_service.ScreenTimeLog")
    def test_create_log_explicit_total_time(self, MockLog):
        """When totalTime is provided it should NOT be overwritten."""
        created = _make_log(totalTime=999)
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "screenId": SCREEN_ID,
            "startTime": "2026-03-15T10:00:00",
            "endTime":   "2026-03-15T10:02:30",
            "totalTime": 999,
        }
        screen_time_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        self.assertEqual(call_kwargs["totalTime"], 999)

    @patch("api.services.screen_time_log_service.ScreenTimeLog")
    def test_create_log_negative_time_clamped(self, MockLog):
        """endTime before startTime should produce totalTime = 0."""
        created = _make_log(totalTime=0)
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "screenId": SCREEN_ID,
            "startTime": "2026-03-15T10:05:00",
            "endTime":   "2026-03-15T10:00:00",
        }
        screen_time_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        self.assertEqual(call_kwargs["totalTime"], 0)


# ===========================================================================
# ScreenTimeLog View Tests
# ===========================================================================

class TestScreenTimeLogViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # --- GET /api/screen-time-logs/ ---

    @patch("api.views.screen_time_log_views.screen_time_log_service")
    def test_list_logs_ok(self, mock_svc):
        mock_svc.list_logs.return_value = [_make_log()]
        req = self.factory.get("/api/screen-time-logs/")
        resp = screen_time_log_collection(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    @patch("api.views.screen_time_log_views.screen_time_log_service")
    def test_list_logs_with_filters(self, mock_svc):
        mock_svc.list_logs.return_value = []
        req = self.factory.get(
            "/api/screen-time-logs/", {"userId": USER_ID, "screenId": SCREEN_ID}
        )
        resp = screen_time_log_collection(req)
        self.assertEqual(resp.status_code, 200)
        mock_svc.list_logs.assert_called_once_with(
            user_id=USER_ID, screen_id=SCREEN_ID
        )

    @patch("api.views.screen_time_log_views.screen_time_log_service")
    def test_list_logs_service_error(self, mock_svc):
        mock_svc.list_logs.side_effect = Exception("DB error")
        req = self.factory.get("/api/screen-time-logs/")
        resp = screen_time_log_collection(req)
        self.assertEqual(resp.status_code, 500)

    # --- POST /api/screen-time-logs/ (requires Firebase auth) ---

    @patch("api.views.screen_time_log_views.screen_time_log_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_log_ok_with_auth(self, mock_auth, mock_svc):
        from api.models import User
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_log.return_value = _make_log()

            payload = {
                "userId": USER_ID,
                "screenId": SCREEN_ID,
                "startTime": "2026-03-15T10:00:00",
                "endTime": "2026-03-15T10:02:30",
            }
            req = self.factory.post(
                "/api/screen-time-logs/",
                json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer valid_token",
            )
            resp = screen_time_log_collection(req)
        self.assertEqual(resp.status_code, 201)

    def test_create_log_no_auth_returns_401(self):
        payload = {"userId": USER_ID, "screenId": SCREEN_ID}
        req = self.factory.post(
            "/api/screen-time-logs/",
            json.dumps(payload),
            content_type="application/json",
        )
        resp = screen_time_log_collection(req)
        self.assertEqual(resp.status_code, 401)

    def test_create_log_invalid_token_returns_401(self):
        """A bad/expired token should produce a 401 from @firebase_required."""
        from firebase_admin import auth as real_auth

        # Raise the real firebase InvalidIdTokenError so the decorator's
        # except block can catch it by its actual class.
        with patch(
            "api.authentication.firebase_authentication.auth"
        ) as mock_auth:
            mock_auth.RevokedIdTokenError    = real_auth.RevokedIdTokenError
            mock_auth.ExpiredIdTokenError    = real_auth.ExpiredIdTokenError
            mock_auth.InvalidIdTokenError    = real_auth.InvalidIdTokenError
            mock_auth.verify_id_token.side_effect = real_auth.InvalidIdTokenError(
                "Invalid token", cause=None, http_response=None
            )

            req = self.factory.post(
                "/api/screen-time-logs/",
                json.dumps({"userId": USER_ID}),
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer bad_token",
            )
            resp = screen_time_log_collection(req)
        self.assertEqual(resp.status_code, 401)

    # --- Method not allowed ---

    def test_screen_time_log_method_not_allowed(self):
        req = self.factory.delete("/api/screen-time-logs/")
        resp = screen_time_log_collection(req)
        self.assertEqual(resp.status_code, 405)


# ===========================================================================
# Serializer Tests
# ===========================================================================

class TestScreenSerializer(TestCase):

    def test_screen_to_dict_no_buttons(self):
        screen = _make_screen(name="TestScreen", hasAds=True, buttons=[])
        result = screen_to_dict(screen)
        self.assertEqual(result["name"], "TestScreen")
        self.assertTrue(result["hasAds"])
        self.assertEqual(result["buttons"], [])
        self.assertIn("id", result)

    def test_screen_to_dict_with_buttons(self):
        btn = MagicMock()
        btn.buttonId = "btn_1"
        btn.schema   = 1
        btn.name     = "Add Pet"
        screen = _make_screen(buttons=[btn])
        result = screen_to_dict(screen)
        self.assertEqual(len(result["buttons"]), 1)
        self.assertEqual(result["buttons"][0]["buttonId"], "btn_1")
        self.assertEqual(result["buttons"][0]["name"], "Add Pet")

    def test_screen_time_log_to_dict(self):
        log = _make_log()
        result = screen_time_log_to_dict(log)
        self.assertEqual(result["userId"], USER_ID)
        self.assertEqual(result["screenId"], SCREEN_ID)
        self.assertEqual(result["totalTime"], 150)
        self.assertIn("startTime", result)
        self.assertIn("endTime", result)
