import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from bson import ObjectId
from rest_framework.test import force_authenticate

from api.views.user_views import MeView, UserDetailView
from api.models import User
from api.services import user_service
from api.serializers.user_serializer import UserSerializer, UserUpdateSerializer, UserPublicSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = str(ObjectId())
OTHER_USER_ID = str(ObjectId())


def _make_user(**kwargs):
    """Create a mock User with realistic defaults (snake_case model attributes)."""
    u = MagicMock(spec=User)
    u.id = ObjectId(kwargs.get("id", USER_ID))
    u.schema = kwargs.get("schema", 1)
    u.firebase_uid = kwargs.get("firebase_uid", "firebase_uid_123")
    u.name = kwargs.get("name", "David Tobon")
    u.email = kwargs.get("email", "david@example.com")
    u.token = kwargs.get("token", "")
    u.phone = kwargs.get("phone", "+573001234567")
    u.address = kwargs.get("address", "Cll 10 #5-30")
    u.profile_photo = kwargs.get("profile_photo", "https://example.com/photo.jpg")
    u.initials = kwargs.get("initials", "DT")
    u.pets = kwargs.get("pets", [])
    u.family_group = kwargs.get("family_group", [ObjectId(USER_ID)])
    u.is_authenticated = True
    u.created_at = "2026-01-01T00:00:00Z"
    u.updated_at = "2026-03-15T00:00:00Z"
    return u


# ===========================================================================
# User Service Tests
# ===========================================================================

class TestUserService(TestCase):

    @patch("api.services.user_service.User")
    def test_create_user(self, MockUser):
        created = _make_user(name="New User")
        MockUser.objects.create.return_value = created
        data = {
            "firebase_uid": "uid_new",
            "name": "New User",
            "email": "new@email.com",
        }
        result = user_service.create_user(data)
        self.assertEqual(result.name, "New User")
        MockUser.objects.create.assert_called_once_with(**data)

    @patch("api.services.user_service.User")
    def test_get_user(self, MockUser):
        expected = _make_user()
        MockUser.objects.get.return_value = expected
        result = user_service.get_user(USER_ID)
        self.assertEqual(result, expected)
        MockUser.objects.get.assert_called_once_with(id=USER_ID)

    @patch("api.services.user_service.User")
    def test_get_user_not_found(self, MockUser):
        MockUser.DoesNotExist = User.DoesNotExist
        MockUser.objects.get.side_effect = User.DoesNotExist
        with self.assertRaises(User.DoesNotExist):
            user_service.get_user("bad_id")

    @patch("api.services.user_service.User")
    def test_update_user(self, MockUser):
        updated = _make_user(name="Updated Name")
        MockUser.objects.filter.return_value.update.return_value = 1
        MockUser.objects.get.return_value = updated
        result = user_service.update_user(USER_ID, {"name": "Updated Name"})
        MockUser.objects.filter.assert_called_once_with(id=USER_ID)
        self.assertEqual(result.name, "Updated Name")

    @patch("api.services.user_service.User")
    def test_delete_user(self, MockUser):
        MockUser.objects.filter.return_value.delete.return_value = None
        user_service.delete_user(USER_ID)
        MockUser.objects.filter.assert_called_once_with(id=USER_ID)
        MockUser.objects.filter.return_value.delete.assert_called_once()


# ===========================================================================
# MeView Tests (DRF APIView with FirebaseAuthentication)
# ===========================================================================

class TestMeView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MeView.as_view()

    def _authenticated_request(self, method, path="/api/users/me/", data=None):
        """Build a request and force-authenticate with a mock user."""
        maker = getattr(self.factory, method)
        if data:
            request = maker(path, json.dumps(data), content_type="application/json")
        else:
            request = maker(path)
        self.mock_user = _make_user()
        force_authenticate(request, user=self.mock_user)
        return request

    # --- GET /api/users/me/ ---

    def test_get_me_ok(self):
        request = self._authenticated_request("get")
        # Patched serializer.data uses camelCase keys (matches new UserSerializer)
        with patch.object(UserSerializer, "data", new_callable=lambda: property(lambda self: {
            "id": USER_ID,
            "schema": 1,
            "firebaseUid": "firebase_uid_123",
            "name": "David Tobon",
            "email": "david@example.com",
            "token": "",
            "phone": "+573001234567",
            "address": "Cll 10 #5-30",
            "profilePhoto": "https://example.com/photo.jpg",
            "initials": "DT",
            "pets": [],
            "familyGroup": [USER_ID],
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-03-15T00:00:00Z",
        })):
            resp = self.view(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "David Tobon")

    def test_get_me_unauthenticated(self):
        request = self.factory.get("/api/users/me/")
        resp = self.view(request)
        self.assertIn(resp.status_code, [401, 403])

    # --- PUT /api/users/me/ ---

    def test_put_me_ok(self):
        # Request body uses camelCase (profilePhoto)
        request = self._authenticated_request("put", data={
            "name": "New Name",
            "phone": "+573009999999",
            "address": "New Address",
            "profilePhoto": "https://example.com/new.jpg",
            "initials": "NN",
        })
        with patch.object(UserUpdateSerializer, "is_valid", return_value=True), \
             patch.object(UserUpdateSerializer, "save", return_value=None), \
             patch.object(UserSerializer, "data", new_callable=lambda: property(lambda self: {
                 "id": USER_ID,
                 "schema": 1,
                 "firebaseUid": "firebase_uid_123",
                 "name": "New Name",
                 "email": "david@example.com",
                 "token": "",
                 "phone": "+573009999999",
                 "address": "New Address",
                 "profilePhoto": "https://example.com/new.jpg",
                 "initials": "NN",
                 "pets": [],
                 "familyGroup": [USER_ID],
                 "createdAt": "2026-01-01T00:00:00Z",
                 "updatedAt": "2026-03-15T00:00:00Z",
             })):
            resp = self.view(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "New Name")

    def test_put_me_invalid_data(self):
        request = self._authenticated_request("put", data={"name": "X"})
        with patch.object(UserUpdateSerializer, "is_valid", return_value=False), \
             patch.object(UserUpdateSerializer, "errors", new_callable=lambda: property(lambda self: {"initials": ["This field is required."]})):
            resp = self.view(request)
        self.assertEqual(resp.status_code, 400)

    # --- PATCH /api/users/me/ ---

    def test_patch_me_ok(self):
        request = self._authenticated_request("patch", data={"name": "Patched"})
        with patch.object(UserUpdateSerializer, "is_valid", return_value=True), \
             patch.object(UserUpdateSerializer, "save", return_value=None), \
             patch.object(UserSerializer, "data", new_callable=lambda: property(lambda self: {
                 "id": USER_ID,
                 "schema": 1,
                 "firebaseUid": "firebase_uid_123",
                 "name": "Patched",
                 "email": "david@example.com",
                 "token": "",
                 "phone": "+573001234567",
                 "address": "Cll 10 #5-30",
                 "profilePhoto": "https://example.com/photo.jpg",
                 "initials": "DT",
                 "pets": [],
                 "familyGroup": [USER_ID],
                 "createdAt": "2026-01-01T00:00:00Z",
                 "updatedAt": "2026-03-15T00:00:00Z",
             })):
            resp = self.view(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "Patched")

    # --- DELETE /api/users/me/ ---

    @patch("api.views.user_views.firebase_auth")
    def test_delete_me_ok(self, mock_firebase_auth):
        mock_firebase_auth.delete_user.return_value = None
        request = self._authenticated_request("delete")
        self.mock_user.delete = MagicMock()
        resp = self.view(request)
        self.assertEqual(resp.status_code, 204)
        self.mock_user.delete.assert_called_once()

    @patch("api.views.user_views.firebase_auth")
    def test_delete_me_firebase_user_not_found(self, mock_firebase_auth):
        """If Firebase user is already gone, we should still delete local."""
        mock_firebase_auth.UserNotFoundError = type("UserNotFoundError", (Exception,), {})
        mock_firebase_auth.delete_user.side_effect = mock_firebase_auth.UserNotFoundError()
        request = self._authenticated_request("delete")
        self.mock_user.delete = MagicMock()
        resp = self.view(request)
        self.assertEqual(resp.status_code, 204)
        self.mock_user.delete.assert_called_once()

    @patch("api.views.user_views.firebase_auth")
    def test_delete_me_firebase_error(self, mock_firebase_auth):
        """If Firebase deletion fails with an unexpected error, return 500."""
        mock_firebase_auth.UserNotFoundError = type("UserNotFoundError", (Exception,), {})
        mock_firebase_auth.delete_user.side_effect = Exception("Firebase error")
        request = self._authenticated_request("delete")
        resp = self.view(request)
        self.assertEqual(resp.status_code, 500)
        self.assertIn("error", resp.data)


# ===========================================================================
# UserDetailView Tests
# ===========================================================================

class TestUserDetailView(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = UserDetailView.as_view()

    # --- GET /api/users/<firebase_uid>/ — same user ---

    def test_get_user_detail_same_user(self):
        request = self.factory.get("/api/users/firebase_uid_123/")
        requester = _make_user()
        force_authenticate(request, user=requester)

        target = _make_user()
        with patch("api.views.user_views.get_object_or_404", return_value=target), \
             patch.object(UserPublicSerializer, "data", new_callable=lambda: property(lambda self: {
                 "id": USER_ID,
                 "name": "David Tobon",
                 "profilePhoto": "https://example.com/photo.jpg",
                 "initials": "DT",
             })):
            resp = self.view(request, firebase_uid="firebase_uid_123")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "David Tobon")

    # --- GET /api/users/<firebase_uid>/ — family group member ---

    def test_get_user_detail_family_member(self):
        request = self.factory.get("/api/users/other_uid/")
        requester = _make_user()
        force_authenticate(request, user=requester)

        target = _make_user(
            id=OTHER_USER_ID,
            firebase_uid="other_uid",
            name="Other User",
            family_group=[ObjectId(USER_ID)],  # corrected kwarg: snake_case
        )

        with patch("api.views.user_views.get_object_or_404", return_value=target), \
             patch.object(UserPublicSerializer, "data", new_callable=lambda: property(lambda self: {
                 "id": OTHER_USER_ID,
                 "name": "Other User",
                 "profilePhoto": "https://example.com/photo.jpg",
                 "initials": "OU",
             })):
            resp = self.view(request, firebase_uid="other_uid")
        self.assertEqual(resp.status_code, 200)

    # --- GET /api/users/<firebase_uid>/ — forbidden (not in family group) ---

    def test_get_user_detail_forbidden(self):
        request = self.factory.get("/api/users/stranger_uid/")
        requester = _make_user()
        force_authenticate(request, user=requester)
        # requester NOT in family_group
        requester = _make_user(id=OTHER_USER_ID, firebase_uid="uid_requester")
        target = _make_user(family_group=[ObjectId(USER_ID)])  # only contains itself

        request = self.factory.get(f"/api/users/{target.firebase_uid}/")
        force_authenticate(request, user=requester)

        with patch("api.views.user_views.User") as MockUser:
            MockUser.objects.get = MagicMock(return_value=target)
            resp = self.view(request, firebase_uid=target.firebase_uid)

        self.assertEqual(resp.status_code, 403)

    # --- GET /api/users/<firebase_uid>/ — unauthenticated ---

    def test_get_user_detail_unauthenticated(self):
        request = self.factory.get("/api/users/firebase_uid_123/")
        resp = self.view(request, firebase_uid="firebase_uid_123")
        self.assertIn(resp.status_code, [401, 403])


# ===========================================================================
# Firebase Authentication Class Tests
# ===========================================================================

class TestFirebaseAuthentication(TestCase):

    def test_authenticate_no_header_returns_none(self):
        from api.authentication.firebase_authentication import FirebaseAuthentication
        authenticator = FirebaseAuthentication()
        request = RequestFactory().get("/api/users/me/")
        result = authenticator.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_non_bearer_returns_none(self):
        from api.authentication.firebase_authentication import FirebaseAuthentication
        authenticator = FirebaseAuthentication()
        request = RequestFactory().get("/api/users/me/", HTTP_AUTHORIZATION="Basic abc123")
        result = authenticator.authenticate(request)
        self.assertIsNone(result)

    @patch("api.authentication.firebase_authentication.auth")
    def test_authenticate_valid_token_existing_user(self, mock_auth):
        from api.authentication.firebase_authentication import FirebaseAuthentication
        mock_auth.verify_id_token.return_value = {
            "uid": "firebase_uid_123",
            "email": "david@example.com",
            "name": "David Tobon",
            "picture": "https://example.com/photo.jpg",
        }
        existing_user = _make_user()
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.DoesNotExist = User.DoesNotExist
            MockUser.objects.get.return_value = existing_user
            authenticator = FirebaseAuthentication()
            request = RequestFactory().get(
                "/api/users/me/",
                HTTP_AUTHORIZATION="Bearer valid_token",
            )
            result = authenticator.authenticate(request)
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user, existing_user)
        self.assertEqual(token, "valid_token")

    @patch("api.authentication.firebase_authentication.auth")
    def test_authenticate_valid_token_new_user(self, mock_auth):
        from api.authentication.firebase_authentication import FirebaseAuthentication
        mock_auth.verify_id_token.return_value = {
            "uid": "new_uid",
            "email": "new@example.com",
            "name": "New User",
            "picture": "",
        }
        new_user = _make_user(firebase_uid="new_uid", name="New User")
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.DoesNotExist = User.DoesNotExist
            MockUser.objects.get.side_effect = User.DoesNotExist
            MockUser.objects.create.return_value = new_user
            authenticator = FirebaseAuthentication()
            request = RequestFactory().get(
                "/api/users/me/",
                HTTP_AUTHORIZATION="Bearer valid_token",
            )
            result = authenticator.authenticate(request)
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user.firebase_uid, "new_uid")
        MockUser.objects.create.assert_called_once()

    @patch("api.authentication.firebase_authentication.auth")
    def test_authenticate_revoked_token(self, mock_auth):
        from api.authentication.firebase_authentication import FirebaseAuthentication
        from rest_framework.exceptions import AuthenticationFailed
        from firebase_admin import auth as real_auth
        mock_auth.RevokedIdTokenError = real_auth.RevokedIdTokenError
        mock_auth.ExpiredIdTokenError = real_auth.ExpiredIdTokenError
        mock_auth.InvalidIdTokenError = real_auth.InvalidIdTokenError
        mock_auth.verify_id_token.side_effect = real_auth.RevokedIdTokenError("Token revoked")
        authenticator = FirebaseAuthentication()
        request = RequestFactory().get(
            "/api/users/me/",
            HTTP_AUTHORIZATION="Bearer revoked_token",
        )
        with self.assertRaises(AuthenticationFailed):
            authenticator.authenticate(request)

    @patch("api.authentication.firebase_authentication.auth")
    def test_authenticate_expired_token(self, mock_auth):
        from api.authentication.firebase_authentication import FirebaseAuthentication
        from rest_framework.exceptions import AuthenticationFailed
        from firebase_admin import auth as real_auth
        mock_auth.RevokedIdTokenError = real_auth.RevokedIdTokenError
        mock_auth.ExpiredIdTokenError = real_auth.ExpiredIdTokenError
        mock_auth.InvalidIdTokenError = real_auth.InvalidIdTokenError
        mock_auth.verify_id_token.side_effect = real_auth.ExpiredIdTokenError(
            "Token expired", cause=None
        )
        authenticator = FirebaseAuthentication()
        request = RequestFactory().get(
            "/api/users/me/",
            HTTP_AUTHORIZATION="Bearer expired_token",
        )
        with self.assertRaises(AuthenticationFailed):
            authenticator.authenticate(request)

    @patch("api.authentication.firebase_authentication.auth")
    def test_authenticate_invalid_token(self, mock_auth):
        from api.authentication.firebase_authentication import FirebaseAuthentication
        from rest_framework.exceptions import AuthenticationFailed
        from firebase_admin import auth as real_auth
        mock_auth.RevokedIdTokenError = real_auth.RevokedIdTokenError
        mock_auth.ExpiredIdTokenError = real_auth.ExpiredIdTokenError
        mock_auth.InvalidIdTokenError = real_auth.InvalidIdTokenError
        mock_auth.verify_id_token.side_effect = real_auth.InvalidIdTokenError(
            "Invalid token", cause=None, http_response=None
        )
        authenticator = FirebaseAuthentication()
        request = RequestFactory().get(
            "/api/users/me/",
            HTTP_AUTHORIZATION="Bearer invalid_token",
        )
        with self.assertRaises(AuthenticationFailed):
            authenticator.authenticate(request)


# ===========================================================================
# Helper Function Tests
# ===========================================================================

class TestMakeInitials(TestCase):

    def test_initials_two_words(self):
        from api.authentication.firebase_authentication import _make_initials
        self.assertEqual(_make_initials("David Tobon"), "DT")

    def test_initials_single_word(self):
        from api.authentication.firebase_authentication import _make_initials
        self.assertEqual(_make_initials("David"), "D")

    def test_initials_empty_string(self):
        from api.authentication.firebase_authentication import _make_initials
        self.assertEqual(_make_initials(""), "")

    def test_initials_three_words(self):
        from api.authentication.firebase_authentication import _make_initials
        self.assertEqual(_make_initials("John Michael Smith"), "JMS")

    def test_initials_max_five(self):
        from api.authentication.firebase_authentication import _make_initials
        result = _make_initials("A B C D E F G")
        self.assertTrue(len(result) <= 5)
