import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId
from django.test import RequestFactory, TestCase

from api.models import Exercise, ExerciseGoal, ExerciseRoute, User
from api.serializers.exercise_serializer import (
    exercise_goal_to_dict,
    exercise_route_to_dict,
    exercise_to_dict,
)
from api.services import exercise_service
from api.views.exercise_views import exercise_collection, exercise_goal, exercise_route


PET_ID = str(ObjectId())
OWNER_ID = str(ObjectId())
EXERCISE_ID = str(ObjectId())


def _make_exercise(**kwargs):
    exercise = MagicMock(spec=Exercise)
    exercise.id = ObjectId(kwargs.get("id", EXERCISE_ID))
    exercise.schema = kwargs.get("schema", 1)
    exercise.pet_id = kwargs.get("pet_id", PET_ID)
    exercise.owner_id = kwargs.get("owner_id", OWNER_ID)
    exercise.type = kwargs.get("type", "Walk")
    exercise.started_at = kwargs.get("started_at", datetime(2026, 5, 22, 8, 0))
    exercise.duration_minutes = kwargs.get("duration_minutes", 20)
    exercise.intensity = kwargs.get("intensity", "medium")
    exercise.distance_km = kwargs.get("distance_km", 1.2)
    exercise.notes = kwargs.get("notes", "morning walk")
    exercise.created_at = kwargs.get("created_at", datetime(2026, 5, 22, 8, 20))
    exercise.updated_at = kwargs.get("updated_at", datetime(2026, 5, 22, 8, 20))
    return exercise


def _auth_request(factory, method, path, payload=None):
    maker = getattr(factory, method)
    return maker(
        path,
        json.dumps(payload) if payload else "",
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer valid_token",
    )


class TestExerciseCompatibility(TestCase):

    def test_shared_serializer_keeps_route_and_retry_fields_out(self):
        payload = exercise_to_dict(_make_exercise())

        self.assertEqual(payload["type"], "Walk")
        self.assertIn("distanceKm", payload)
        self.assertNotIn("route", payload)
        self.assertNotIn("points", payload)
        self.assertNotIn("clientMutationId", payload)

    @patch("api.services.exercise_service.Exercise")
    @patch("api.services.exercise_service.Pet")
    def test_optional_mutation_id_deduplicates_offline_create(self, MockPet, MockExercise):
        existing = _make_exercise()
        user = MagicMock(id=OWNER_ID, pets=[PET_ID])
        MockPet.objects.get.return_value = MagicMock(id=ObjectId(PET_ID), birth_date=None)
        MockExercise.objects.filter.return_value.first.return_value = existing

        result = exercise_service.create_exercise(
            user,
            PET_ID,
            {
                "type": "Walk",
                "startedAt": "2026-05-22T08:00:00Z",
                "durationMinutes": 20,
                "intensity": "medium",
                "clientMutationId": "retry-1",
            },
        )

        self.assertEqual(result, existing)
        MockExercise.objects.create.assert_not_called()

    def test_goal_and_route_serializers_are_separate(self):
        goal = MagicMock(spec=ExerciseGoal, weekly_goal_minutes=180)
        route = MagicMock(
            spec=ExerciseRoute,
            points=[{"latitude": 4.6, "longitude": -74.1, "recordedAt": "2026-05-22T08:00:00Z"}],
        )

        self.assertEqual(exercise_goal_to_dict(PET_ID, goal)["weeklyGoalMinutes"], 180)
        self.assertEqual(exercise_goal_to_dict(PET_ID, None)["weeklyGoalMinutes"], 150)
        self.assertEqual(exercise_route_to_dict(PET_ID, EXERCISE_ID, route)["points"], route.points)


class TestExerciseExtensionViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _auth_user(self, mock_auth, MockUser):
        user = MagicMock(spec=User)
        user.firebase_uid = "uid123"
        user.pets = [PET_ID]
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}
        MockUser.objects.get.return_value = user

    @patch("api.views.exercise_views.exercise_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_flutter_style_exercise_create_needs_no_route_or_mutation_id(self, mock_auth, mock_service):
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            self._auth_user(mock_auth, MockUser)
            mock_service.create_exercise.return_value = _make_exercise()
            payload = {
                "type": "Play",
                "startedAt": "2026-05-22T08:00:00Z",
                "durationMinutes": 10,
                "intensity": "medium",
                "distanceKm": None,
                "notes": "",
            }
            request = _auth_request(
                self.factory,
                "post",
                f"/api/pets/{PET_ID}/exercises/",
                payload,
            )
            response = exercise_collection(request, pet_id=PET_ID)

        body = json.loads(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(mock_service.create_exercise.call_args.args[2], payload)
        self.assertNotIn("points", body)
        self.assertNotIn("clientMutationId", body)

    @patch("api.views.exercise_views.exercise_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_goal_put_is_separate_from_exercise_payload(self, mock_auth, mock_service):
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            self._auth_user(mock_auth, MockUser)
            mock_service.update_exercise_goal.return_value = MagicMock(weekly_goal_minutes=210)
            request = _auth_request(
                self.factory,
                "put",
                f"/api/pets/{PET_ID}/exercise-goal/",
                {"weeklyGoalMinutes": 210},
            )
            response = exercise_goal(request, pet_id=PET_ID)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["weeklyGoalMinutes"], 210)

    @patch("api.views.exercise_views.exercise_service")
    @patch("api.authentication.firebase_authentication.auth")
    def test_route_get_can_return_no_points(self, mock_auth, mock_service):
        with patch("api.authentication.firebase_authentication.User") as MockUser:
            self._auth_user(mock_auth, MockUser)
            mock_service.get_exercise_route.return_value = None
            request = _auth_request(
                self.factory,
                "get",
                f"/api/pets/{PET_ID}/exercises/{EXERCISE_ID}/route/",
            )
            response = exercise_route(request, pet_id=PET_ID, exercise_id=EXERCISE_ID)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["points"], [])
