import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from bson import ObjectId

from api.views.feature_views import feature_collection, feature_detail
from api.views.feature_route_views import feature_route_collection, feature_route_detail
from api.views.feature_execution_log_views import feature_execution_log_collection
from api.views.feature_clicks_log_views import feature_clicks_log_collection
from api.models import Feature, FeatureRoute, FeatureExecutionLog, FeatureClicksLog
from api.services import (
    feature_service,
    feature_route_service,
    feature_execution_log_service,
    feature_clicks_log_service,
)
from api.serializers.feature_serializer import feature_to_dict
from api.serializers.feature_route_serializer import feature_route_to_dict
from api.serializers.feature_execution_log_serializer import feature_execution_log_to_dict
from api.serializers.feature_clicks_log_serializer import feature_clicks_log_to_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FEATURE_ID = str(ObjectId())
ROUTE_ID   = str(ObjectId())
USER_ID    = str(ObjectId())
SCREEN_ID  = str(ObjectId())


def _make_feature(**kwargs):
    f = MagicMock(spec=Feature)
    f.id           = ObjectId(FEATURE_ID)
    f.schema       = kwargs.get("schema", 1)
    f.name         = kwargs.get("name", "AddPetFeature")
    f.originButton = kwargs.get("originButton", "btn_add")
    f.originScreen = kwargs.get("originScreen", SCREEN_ID)
    f.appType      = kwargs.get("appType", "Kotlin")
    return f


def _make_route(**kwargs):
    r = MagicMock(spec=FeatureRoute)
    r.id           = ObjectId(ROUTE_ID)
    r.schema       = kwargs.get("schema", 1)
    r.name         = kwargs.get("name", "HomeToProfile")
    r.originButton = kwargs.get("originButton", "btn_home")
    r.originScreen = kwargs.get("originScreen", SCREEN_ID)
    r.endButton    = kwargs.get("endButton", "btn_profile")
    r.endScreen    = kwargs.get("endScreen", SCREEN_ID)
    return r


def _make_exec_log(**kwargs):
    from datetime import datetime, timezone
    log = MagicMock(spec=FeatureExecutionLog)
    log.id            = ObjectId()
    log.schema        = 1
    log.userId        = kwargs.get("userId", USER_ID)
    log.featureId     = kwargs.get("featureId", FEATURE_ID)
    log.startTime     = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    log.endTime       = datetime(2026, 3, 15, 10, 0, 5, tzinfo=timezone.utc)
    log.totalTime     = kwargs.get("totalTime", 5)
    log.downloadSpeed = kwargs.get("downloadSpeed", 100)
    log.uploadSpeed   = kwargs.get("uploadSpeed", 50)
    return log


def _make_clicks_log(**kwargs):
    from datetime import datetime, timezone
    log = MagicMock(spec=FeatureClicksLog)
    log.id        = ObjectId()
    log.schema    = 1
    log.userId    = kwargs.get("userId", USER_ID)
    log.routeId   = kwargs.get("routeId", ROUTE_ID)
    log.timestamp = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    log.nClicks   = kwargs.get("nClicks", 3)
    return log


def _auth_request(factory, method, path, payload=None, token="valid_token"):
    """Build an authenticated request with an HTTP_AUTHORIZATION header."""
    body = json.dumps(payload) if payload else ""
    maker = getattr(factory, method)
    return maker(
        path, body, content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


# ===========================================================================
# Feature Service Tests
# ===========================================================================

class TestFeatureService(TestCase):

    @patch("api.services.feature_service.Feature")
    def test_list_features(self, MockFeature):
        MockFeature.objects.all.return_value = [_make_feature()]
        result = feature_service.list_features()
        self.assertEqual(len(result), 1)
        MockFeature.objects.all.assert_called_once()

    @patch("api.services.feature_service.Feature")
    def test_get_feature_found(self, MockFeature):
        expected = _make_feature()
        MockFeature.objects.get.return_value = expected
        result = feature_service.get_feature(FEATURE_ID)
        self.assertEqual(result, expected)
        MockFeature.objects.get.assert_called_once_with(id=FEATURE_ID)

    @patch("api.services.feature_service.Feature")
    def test_get_feature_not_found_raises(self, MockFeature):
        MockFeature.DoesNotExist = Feature.DoesNotExist
        MockFeature.objects.get.side_effect = Feature.DoesNotExist
        with self.assertRaises(Feature.DoesNotExist):
            feature_service.get_feature("bad_id")

    @patch("api.services.feature_service.Feature")
    def test_create_feature(self, MockFeature):
        created = _make_feature(name="VaccineFeature")
        MockFeature.objects.create.return_value = created
        result = feature_service.create_feature({"name": "VaccineFeature", "appType": "Kotlin"})
        self.assertEqual(result.name, "VaccineFeature")

    @patch("api.services.feature_service.Feature")
    def test_update_feature(self, MockFeature):
        feature = _make_feature(name="Old")
        updated = _make_feature(name="New")
        MockFeature.objects.get.side_effect = [feature, updated]
        result = feature_service.update_feature(FEATURE_ID, {"name": "New"})
        feature.save.assert_called_once()
        self.assertEqual(result.name, "New")

    @patch("api.services.feature_service.Feature")
    def test_delete_feature(self, MockFeature):
        MockFeature.objects.filter.return_value.delete.return_value = None
        feature_service.delete_feature(FEATURE_ID)
        MockFeature.objects.filter.assert_called_once_with(id=FEATURE_ID)
        MockFeature.objects.filter.return_value.delete.assert_called_once()


# ===========================================================================
# Feature View Tests
# ===========================================================================

class TestFeatureViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # --- GET /api/features/ ---

    @patch("api.views.feature_views.feature_service")
    def test_list_features_ok(self, mock_svc):
        mock_svc.list_features.return_value = [_make_feature()]
        req = self.factory.get("/api/features/")
        resp = feature_collection(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["name"], "AddPetFeature")

    @patch("api.views.feature_views.feature_service")
    def test_list_features_empty(self, mock_svc):
        mock_svc.list_features.return_value = []
        req = self.factory.get("/api/features/")
        resp = feature_collection(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), [])

    @patch("api.views.feature_views.feature_service")
    def test_list_features_service_error(self, mock_svc):
        mock_svc.list_features.side_effect = Exception("DB error")
        req = self.factory.get("/api/features/")
        resp = feature_collection(req)
        self.assertEqual(resp.status_code, 500)

    # --- POST /api/features/ ---

    @patch("api.views.feature_views.feature_service")
    def test_create_feature_ok(self, mock_svc):
        mock_svc.create_feature.return_value = _make_feature(name="NfcFeature")
        payload = {"name": "NfcFeature", "appType": "Kotlin", "originButton": "btn_nfc",
                   "originScreen": SCREEN_ID}
        req = self.factory.post("/api/features/", json.dumps(payload), content_type="application/json")
        resp = feature_collection(req)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json.loads(resp.content)["name"], "NfcFeature")

    @patch("api.views.feature_views.feature_service")
    def test_create_feature_invalid_json(self, mock_svc):
        req = self.factory.post("/api/features/", "not-json", content_type="application/json")
        resp = feature_collection(req)
        self.assertEqual(resp.status_code, 400)

    @patch("api.views.feature_views.feature_service")
    def test_create_feature_service_error(self, mock_svc):
        mock_svc.create_feature.side_effect = Exception("Constraint error")
        req = self.factory.post("/api/features/", json.dumps({"name": "X"}),
                                content_type="application/json")
        resp = feature_collection(req)
        self.assertEqual(resp.status_code, 400)

    def test_feature_collection_method_not_allowed(self):
        req = self.factory.put("/api/features/")
        resp = feature_collection(req)
        self.assertEqual(resp.status_code, 405)

    # --- GET /api/features/<id>/ ---

    @patch("api.views.feature_views.feature_service")
    def test_get_feature_detail_ok(self, mock_svc):
        mock_svc.get_feature.return_value = _make_feature()
        req = self.factory.get(f"/api/features/{FEATURE_ID}/")
        resp = feature_detail(req, feature_id=FEATURE_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["id"], FEATURE_ID)

    @patch("api.views.feature_views.feature_service")
    def test_get_feature_detail_not_found(self, mock_svc):
        mock_svc.get_feature.side_effect = Feature.DoesNotExist
        req = self.factory.get("/api/features/badid/")
        resp = feature_detail(req, feature_id="badid")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Feature not found", json.loads(resp.content)["error"])

    # --- PUT /api/features/<id>/ ---

    @patch("api.views.feature_views.feature_service")
    def test_update_feature_ok(self, mock_svc):
        mock_svc.update_feature.return_value = _make_feature(name="Updated")
        req = self.factory.put(f"/api/features/{FEATURE_ID}/",
                               json.dumps({"name": "Updated"}),
                               content_type="application/json")
        resp = feature_detail(req, feature_id=FEATURE_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["name"], "Updated")

    @patch("api.views.feature_views.feature_service")
    def test_update_feature_not_found(self, mock_svc):
        mock_svc.update_feature.side_effect = Feature.DoesNotExist
        req = self.factory.put("/api/features/badid/",
                               json.dumps({"name": "X"}),
                               content_type="application/json")
        resp = feature_detail(req, feature_id="badid")
        self.assertEqual(resp.status_code, 404)

    # --- DELETE /api/features/<id>/ ---

    @patch("api.views.feature_views.feature_service")
    def test_delete_feature_ok(self, mock_svc):
        mock_svc.delete_feature.return_value = None
        req = self.factory.delete(f"/api/features/{FEATURE_ID}/")
        resp = feature_detail(req, feature_id=FEATURE_ID)
        self.assertEqual(resp.status_code, 204)

    @patch("api.views.feature_views.feature_service")
    def test_delete_feature_not_found(self, mock_svc):
        mock_svc.delete_feature.side_effect = Feature.DoesNotExist
        req = self.factory.delete("/api/features/badid/")
        resp = feature_detail(req, feature_id="badid")
        self.assertEqual(resp.status_code, 404)

    def test_feature_detail_method_not_allowed(self):
        req = self.factory.patch(f"/api/features/{FEATURE_ID}/")
        resp = feature_detail(req, feature_id=FEATURE_ID)
        self.assertEqual(resp.status_code, 405)


# ===========================================================================
# FeatureRoute Service Tests
# ===========================================================================

class TestFeatureRouteService(TestCase):

    @patch("api.services.feature_route_service.FeatureRoute")
    def test_list_feature_routes(self, MockRoute):
        MockRoute.objects.all.return_value = [_make_route()]
        result = feature_route_service.list_feature_routes()
        self.assertEqual(len(result), 1)

    @patch("api.services.feature_route_service.FeatureRoute")
    def test_get_feature_route_found(self, MockRoute):
        expected = _make_route()
        MockRoute.objects.get.return_value = expected
        result = feature_route_service.get_feature_route(ROUTE_ID)
        self.assertEqual(result, expected)

    @patch("api.services.feature_route_service.FeatureRoute")
    def test_get_feature_route_not_found(self, MockRoute):
        MockRoute.DoesNotExist = FeatureRoute.DoesNotExist
        MockRoute.objects.get.side_effect = FeatureRoute.DoesNotExist
        with self.assertRaises(FeatureRoute.DoesNotExist):
            feature_route_service.get_feature_route("bad_id")

    @patch("api.services.feature_route_service.FeatureRoute")
    def test_create_feature_route(self, MockRoute):
        created = _make_route(name="NewRoute")
        MockRoute.objects.create.return_value = created
        result = feature_route_service.create_feature_route({"name": "NewRoute"})
        self.assertEqual(result.name, "NewRoute")

    @patch("api.services.feature_route_service.FeatureRoute")
    def test_update_feature_route(self, MockRoute):
        route = _make_route(name="OldRoute")
        updated = _make_route(name="UpdatedRoute")
        MockRoute.objects.get.side_effect = [route, updated]
        result = feature_route_service.update_feature_route(ROUTE_ID, {"name": "UpdatedRoute"})
        route.save.assert_called_once()
        self.assertEqual(result.name, "UpdatedRoute")

    @patch("api.services.feature_route_service.FeatureRoute")
    def test_delete_feature_route(self, MockRoute):
        MockRoute.objects.filter.return_value.delete.return_value = None
        feature_route_service.delete_feature_route(ROUTE_ID)
        MockRoute.objects.filter.assert_called_once_with(id=ROUTE_ID)


# ===========================================================================
# FeatureRoute View Tests
# ===========================================================================

class TestFeatureRouteViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch("api.views.feature_route_views.feature_route_service")
    def test_list_routes_ok(self, mock_svc):
        mock_svc.list_feature_routes.return_value = [_make_route()]
        req = self.factory.get("/api/feature-routes/")
        resp = feature_route_collection(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(json.loads(resp.content)), 1)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_list_routes_service_error(self, mock_svc):
        mock_svc.list_feature_routes.side_effect = Exception("fail")
        req = self.factory.get("/api/feature-routes/")
        resp = feature_route_collection(req)
        self.assertEqual(resp.status_code, 500)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_create_route_ok(self, mock_svc):
        mock_svc.create_feature_route.return_value = _make_route(name="NewRoute")
        payload = {"name": "NewRoute", "originButton": "btn_a", "originScreen": SCREEN_ID,
                   "endButton": "btn_b", "endScreen": SCREEN_ID}
        req = self.factory.post("/api/feature-routes/", json.dumps(payload),
                                content_type="application/json")
        resp = feature_route_collection(req)
        self.assertEqual(resp.status_code, 201)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_create_route_invalid_json(self, mock_svc):
        req = self.factory.post("/api/feature-routes/", "bad", content_type="application/json")
        resp = feature_route_collection(req)
        self.assertEqual(resp.status_code, 400)

    def test_route_collection_method_not_allowed(self):
        req = self.factory.delete("/api/feature-routes/")
        resp = feature_route_collection(req)
        self.assertEqual(resp.status_code, 405)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_get_route_detail_ok(self, mock_svc):
        mock_svc.get_feature_route.return_value = _make_route()
        req = self.factory.get(f"/api/feature-routes/{ROUTE_ID}/")
        resp = feature_route_detail(req, route_id=ROUTE_ID)
        self.assertEqual(resp.status_code, 200)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_get_route_detail_not_found(self, mock_svc):
        mock_svc.get_feature_route.side_effect = FeatureRoute.DoesNotExist
        req = self.factory.get("/api/feature-routes/badid/")
        resp = feature_route_detail(req, route_id="badid")
        self.assertEqual(resp.status_code, 404)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_update_route_ok(self, mock_svc):
        mock_svc.update_feature_route.return_value = _make_route(name="Updated")
        req = self.factory.put(f"/api/feature-routes/{ROUTE_ID}/",
                               json.dumps({"name": "Updated"}),
                               content_type="application/json")
        resp = feature_route_detail(req, route_id=ROUTE_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["name"], "Updated")

    @patch("api.views.feature_route_views.feature_route_service")
    def test_update_route_not_found(self, mock_svc):
        mock_svc.update_feature_route.side_effect = FeatureRoute.DoesNotExist
        req = self.factory.put("/api/feature-routes/badid/",
                               json.dumps({"name": "X"}),
                               content_type="application/json")
        resp = feature_route_detail(req, route_id="badid")
        self.assertEqual(resp.status_code, 404)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_delete_route_ok(self, mock_svc):
        mock_svc.delete_feature_route.return_value = None
        req = self.factory.delete(f"/api/feature-routes/{ROUTE_ID}/")
        resp = feature_route_detail(req, route_id=ROUTE_ID)
        self.assertEqual(resp.status_code, 204)

    @patch("api.views.feature_route_views.feature_route_service")
    def test_delete_route_not_found(self, mock_svc):
        mock_svc.delete_feature_route.side_effect = FeatureRoute.DoesNotExist
        req = self.factory.delete("/api/feature-routes/badid/")
        resp = feature_route_detail(req, route_id="badid")
        self.assertEqual(resp.status_code, 404)

    def test_route_detail_method_not_allowed(self):
        req = self.factory.patch(f"/api/feature-routes/{ROUTE_ID}/")
        resp = feature_route_detail(req, route_id=ROUTE_ID)
        self.assertEqual(resp.status_code, 405)


# ===========================================================================
# FeatureExecutionLog Service Tests
# ===========================================================================

class TestFeatureExecutionLogService(TestCase):

    @patch("api.services.feature_execution_log_service.FeatureExecutionLog")
    def test_list_logs_no_filter(self, MockLog):
        MockLog.objects.all.return_value = []
        result = feature_execution_log_service.list_logs()
        self.assertEqual(result, [])

    @patch("api.services.feature_execution_log_service.FeatureExecutionLog")
    def test_list_logs_filter_user(self, MockLog):
        qs = MagicMock()
        MockLog.objects.all.return_value = qs
        qs.filter.return_value = qs
        feature_execution_log_service.list_logs(user_id=USER_ID)
        qs.filter.assert_called_with(userId=USER_ID)

    @patch("api.services.feature_execution_log_service.FeatureExecutionLog")
    def test_list_logs_filter_feature(self, MockLog):
        qs = MagicMock()
        MockLog.objects.all.return_value = qs
        qs.filter.return_value = qs
        feature_execution_log_service.list_logs(feature_id=FEATURE_ID)
        qs.filter.assert_called_with(featureId=FEATURE_ID)

    @patch("api.services.feature_execution_log_service.FeatureExecutionLog")
    def test_create_log_auto_total_time(self, MockLog):
        created = _make_exec_log(totalTime=5)
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "featureId": FEATURE_ID,
            "startTime": "2026-03-15T10:00:00",
            "endTime":   "2026-03-15T10:00:05",
            "downloadSpeed": 100,
            "uploadSpeed": 50,
        }
        feature_execution_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        self.assertEqual(call_kwargs["totalTime"], 5)

    @patch("api.services.feature_execution_log_service.FeatureExecutionLog")
    def test_create_log_explicit_total_time_preserved(self, MockLog):
        created = _make_exec_log(totalTime=42)
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "featureId": FEATURE_ID,
            "startTime": "2026-03-15T10:00:00",
            "endTime":   "2026-03-15T10:00:05",
            "totalTime": 42,
            "downloadSpeed": 100,
            "uploadSpeed": 50,
        }
        feature_execution_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        self.assertEqual(call_kwargs["totalTime"], 42)

    @patch("api.services.feature_execution_log_service.FeatureExecutionLog")
    def test_create_log_negative_time_clamped(self, MockLog):
        created = _make_exec_log(totalTime=0)
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "featureId": FEATURE_ID,
            "startTime": "2026-03-15T10:05:00",
            "endTime":   "2026-03-15T10:00:00",
        }
        feature_execution_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        self.assertEqual(call_kwargs["totalTime"], 0)


# ===========================================================================
# FeatureExecutionLog View Tests
# ===========================================================================

class TestFeatureExecutionLogViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch("api.views.feature_execution_log_views.feature_execution_log_service")
    def test_list_logs_ok(self, mock_svc):
        mock_svc.list_logs.return_value = [_make_exec_log()]
        req = self.factory.get("/api/feature-execution-logs/")
        resp = feature_execution_log_collection(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(json.loads(resp.content)), 1)

    @patch("api.views.feature_execution_log_views.feature_execution_log_service")
    def test_list_logs_with_query_params(self, mock_svc):
        mock_svc.list_logs.return_value = []
        req = self.factory.get(
            "/api/feature-execution-logs/",
            {"userId": USER_ID, "featureId": FEATURE_ID}
        )
        resp = feature_execution_log_collection(req)
        self.assertEqual(resp.status_code, 200)
        mock_svc.list_logs.assert_called_once_with(
            user_id=USER_ID, feature_id=FEATURE_ID
        )

    @patch("api.views.feature_execution_log_views.feature_execution_log_service")
    def test_list_logs_service_error(self, mock_svc):
        mock_svc.list_logs.side_effect = Exception("DB down")
        req = self.factory.get("/api/feature-execution-logs/")
        resp = feature_execution_log_collection(req)
        self.assertEqual(resp.status_code, 500)

    @patch("api.views.feature_execution_log_views.feature_execution_log_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_exec_log_ok_with_auth(self, mock_auth, mock_svc):
        from api.models import User
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_log.return_value = _make_exec_log()

            payload = {
                "userId": USER_ID,
                "featureId": FEATURE_ID,
                "startTime": "2026-03-15T10:00:00",
                "endTime": "2026-03-15T10:00:05",
                "downloadSpeed": 100,
                "uploadSpeed": 50,
            }
            req = self.factory.post(
                "/api/feature-execution-logs/",
                json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer valid_token",
            )
            resp = feature_execution_log_collection(req)
        self.assertEqual(resp.status_code, 201)

    def test_create_exec_log_no_auth_returns_401(self):
        req = self.factory.post(
            "/api/feature-execution-logs/",
            json.dumps({"userId": USER_ID}),
            content_type="application/json",
        )
        resp = feature_execution_log_collection(req)
        self.assertEqual(resp.status_code, 401)

    def test_exec_log_method_not_allowed(self):
        req = self.factory.delete("/api/feature-execution-logs/")
        resp = feature_execution_log_collection(req)
        self.assertEqual(resp.status_code, 405)


# ===========================================================================
# FeatureClicksLog Service Tests
# ===========================================================================

class TestFeatureClicksLogService(TestCase):

    @patch("api.services.feature_clicks_log_service.FeatureClicksLog")
    def test_list_logs_no_filter(self, MockLog):
        MockLog.objects.all.return_value = []
        result = feature_clicks_log_service.list_logs()
        self.assertEqual(result, [])

    @patch("api.services.feature_clicks_log_service.FeatureClicksLog")
    def test_list_logs_filter_user(self, MockLog):
        qs = MagicMock()
        MockLog.objects.all.return_value = qs
        qs.filter.return_value = qs
        feature_clicks_log_service.list_logs(user_id=USER_ID)
        qs.filter.assert_called_with(userId=USER_ID)

    @patch("api.services.feature_clicks_log_service.FeatureClicksLog")
    def test_list_logs_filter_route(self, MockLog):
        qs = MagicMock()
        MockLog.objects.all.return_value = qs
        qs.filter.return_value = qs
        feature_clicks_log_service.list_logs(route_id=ROUTE_ID)
        qs.filter.assert_called_with(routeId=ROUTE_ID)

    @patch("api.services.feature_clicks_log_service.FeatureClicksLog")
    def test_create_clicks_log_parses_timestamp(self, MockLog):
        created = _make_clicks_log()
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "routeId": ROUTE_ID,
            "timestamp": "2026-03-15T10:00:00Z",
            "nClicks": 3,
        }
        feature_clicks_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        # timestamp should be a datetime, not a string
        from datetime import datetime
        self.assertIsInstance(call_kwargs["timestamp"], datetime)

    @patch("api.services.feature_clicks_log_service.FeatureClicksLog")
    def test_create_clicks_log_stores_nclicks(self, MockLog):
        created = _make_clicks_log(nClicks=7)
        MockLog.objects.create.return_value = created
        data = {
            "userId": USER_ID,
            "routeId": ROUTE_ID,
            "timestamp": "2026-03-15T10:00:00",
            "nClicks": 7,
        }
        feature_clicks_log_service.create_log(data)
        call_kwargs = MockLog.objects.create.call_args[1]
        self.assertEqual(call_kwargs["nClicks"], 7)


# ===========================================================================
# FeatureClicksLog View Tests
# ===========================================================================

class TestFeatureClicksLogViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch("api.views.feature_clicks_log_views.feature_clicks_log_service")
    def test_list_clicks_logs_ok(self, mock_svc):
        mock_svc.list_logs.return_value = [_make_clicks_log()]
        req = self.factory.get("/api/feature-clicks-logs/")
        resp = feature_clicks_log_collection(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data[0]["nClicks"], 3)

    @patch("api.views.feature_clicks_log_views.feature_clicks_log_service")
    def test_list_clicks_logs_with_query_params(self, mock_svc):
        mock_svc.list_logs.return_value = []
        req = self.factory.get(
            "/api/feature-clicks-logs/",
            {"userId": USER_ID, "routeId": ROUTE_ID}
        )
        resp = feature_clicks_log_collection(req)
        self.assertEqual(resp.status_code, 200)
        mock_svc.list_logs.assert_called_once_with(
            user_id=USER_ID, route_id=ROUTE_ID
        )

    @patch("api.views.feature_clicks_log_views.feature_clicks_log_service")
    def test_list_clicks_logs_service_error(self, mock_svc):
        mock_svc.list_logs.side_effect = Exception("fail")
        req = self.factory.get("/api/feature-clicks-logs/")
        resp = feature_clicks_log_collection(req)
        self.assertEqual(resp.status_code, 500)

    @patch("api.views.feature_clicks_log_views.feature_clicks_log_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_create_clicks_log_ok_with_auth(self, mock_auth, mock_svc):
        from api.models import User
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            mock_svc.create_log.return_value = _make_clicks_log()

            payload = {
                "userId": USER_ID,
                "routeId": ROUTE_ID,
                "timestamp": "2026-03-15T10:00:00",
                "nClicks": 5,
            }
            req = self.factory.post(
                "/api/feature-clicks-logs/",
                json.dumps(payload),
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer valid_token",
            )
            resp = feature_clicks_log_collection(req)
        self.assertEqual(resp.status_code, 201)

    def test_create_clicks_log_no_auth_returns_401(self):
        req = self.factory.post(
            "/api/feature-clicks-logs/",
            json.dumps({"userId": USER_ID}),
            content_type="application/json",
        )
        resp = feature_clicks_log_collection(req)
        self.assertEqual(resp.status_code, 401)

    def test_clicks_log_method_not_allowed(self):
        req = self.factory.put("/api/feature-clicks-logs/")
        resp = feature_clicks_log_collection(req)
        self.assertEqual(resp.status_code, 405)


# ===========================================================================
# Serializer Tests
# ===========================================================================

class TestFeatureSerializers(TestCase):

    def test_feature_to_dict(self):
        f = _make_feature()
        result = feature_to_dict(f)
        self.assertEqual(result["id"], FEATURE_ID)
        self.assertEqual(result["name"], "AddPetFeature")
        self.assertEqual(result["appType"], "Kotlin")
        self.assertIn("originButton", result)
        self.assertIn("originScreen", result)

    def test_feature_route_to_dict(self):
        r = _make_route()
        result = feature_route_to_dict(r)
        self.assertEqual(result["id"], ROUTE_ID)
        self.assertIn("originButton", result)
        self.assertIn("originScreen", result)
        self.assertIn("endButton", result)
        self.assertIn("endScreen", result)

    def test_feature_execution_log_to_dict(self):
        log = _make_exec_log(downloadSpeed=200, uploadSpeed=80)
        result = feature_execution_log_to_dict(log)
        self.assertEqual(result["downloadSpeed"], 200)
        self.assertEqual(result["uploadSpeed"], 80)
        self.assertIn("startTime", result)
        self.assertIn("endTime", result)
        self.assertIn("totalTime", result)

    def test_feature_clicks_log_to_dict(self):
        log = _make_clicks_log(nClicks=5)
        result = feature_clicks_log_to_dict(log)
        self.assertEqual(result["nClicks"], 5)
        self.assertIn("timestamp", result)
        self.assertIn("routeId", result)
