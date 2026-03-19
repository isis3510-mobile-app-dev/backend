import json
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from bson import ObjectId
from django.test import RequestFactory, TestCase

from api.models import Pet, User, Vaccine
from api.services.smart_vaccination_service import analyze_pet_vaccines
from api.views.smart_vaccination_view import pet_smart_view

SERVICE = "api.services.smart_vaccination_service"
PET_ID = str(ObjectId())


def make_vaccination(vaccine_id="abc123", days_offset=None, next_due_date=None):
    vaccination = MagicMock()
    vaccination.vaccine_id = vaccine_id
    vaccination.date_given = None
    if next_due_date is not None:
        vaccination.next_due_date = next_due_date
    elif days_offset is not None:
        vaccination.next_due_date = date.today() + timedelta(days=days_offset)
    else:
        vaccination.next_due_date = None
    return vaccination


def make_catalog_vaccine(vaccine_id, name, interval_days=365, product_name=""):
    vaccine = MagicMock(spec=Vaccine)
    vaccine.id = vaccine_id
    vaccine.name = name
    vaccine.product_name = product_name
    vaccine.interval_days = interval_days
    vaccine.species = ["dog"]
    return vaccine


def make_pet(vaccinations, species="dog", birth_date=None):
    pet = MagicMock(spec=Pet)
    pet.id = PET_ID
    pet.name = "Luna"
    pet.species = species
    pet.birth_date = birth_date
    pet.vaccinations = vaccinations
    return pet


def make_event(
    *,
    title="Vet check",
    event_type="vet_visit",
    days_ago=200,
):
    event = MagicMock()
    event.title = title
    event.event_type = event_type
    event.date = datetime.combine(
        date.today() - timedelta(days=days_ago),
        datetime.min.time(),
    )
    return event


def _auth_request(factory, path, token="valid_token"):
    return factory.get(
        path,
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


class TestAnalyzePetVaccinesExisting(TestCase):
    def _run(self, vaccinations, vaccine_name="Rabies", catalog=None):
        pet = make_pet(vaccinations)
        catalog = catalog or []
        with patch(f"{SERVICE}.Pet.objects.get", return_value=pet), \
             patch(f"{SERVICE}.Vaccine.objects.get") as mock_get, \
             patch(f"{SERVICE}.Vaccine.objects.all", return_value=catalog), \
             patch(f"{SERVICE}.Event.objects.filter", return_value=[make_event(days_ago=90)]):
            mock_vaccine = MagicMock()
            mock_vaccine.name = vaccine_name
            mock_get.return_value = mock_vaccine
            _, suggestions = analyze_pet_vaccines(PET_ID)
        return suggestions

    def test_vaccine_overdue_more_than_30_days_returns_danger(self):
        suggestions = self._run([make_vaccination(days_offset=-45)])
        danger = next(s for s in suggestions if s["type"] == "danger")
        self.assertIn("45", danger["message"])

    def test_vaccine_overdue_less_than_30_days_returns_warning(self):
        suggestions = self._run([make_vaccination(days_offset=-10)])
        self.assertTrue(any(s["type"] == "warning" for s in suggestions))

    def test_vaccine_due_within_30_days_returns_info(self):
        suggestions = self._run([make_vaccination(days_offset=15)])
        self.assertTrue(any(s["type"] == "info" for s in suggestions))

    def test_vaccine_not_due_soon_returns_no_vaccine_suggestion(self):
        suggestions = self._run([make_vaccination(days_offset=60)])
        vaccine_suggestions = [s for s in suggestions if "Vaccine" in s["title"]]
        self.assertEqual(vaccine_suggestions, [])

    def test_vaccination_without_next_due_date_is_skipped(self):
        suggestions = self._run([make_vaccination(next_due_date=None)])
        vaccine_suggestions = [s for s in suggestions if "Vaccine" in s["title"]]
        self.assertEqual(vaccine_suggestions, [])

    def test_unknown_vaccine_id_falls_back_to_id_string(self):
        pet = make_pet([make_vaccination(vaccine_id="unknown_id", days_offset=-45)])
        with patch(f"{SERVICE}.Pet.objects.get", return_value=pet), \
             patch(f"{SERVICE}.Vaccine.objects.get", side_effect=Vaccine.DoesNotExist), \
             patch(f"{SERVICE}.Vaccine.objects.all", return_value=[]), \
             patch(f"{SERVICE}.Event.objects.filter", return_value=[make_event(days_ago=90)]):
            _, suggestions = analyze_pet_vaccines(PET_ID)
        self.assertIn("unknown_id", suggestions[0]["title"])


class TestAnalyzeMissingVaccines(TestCase):
    def _run(self, vaccinations, catalog_vaccines, species="dog", birth_date=None):
        pet = make_pet(vaccinations, species=species, birth_date=birth_date)
        with patch(f"{SERVICE}.Pet.objects.get", return_value=pet), \
             patch(f"{SERVICE}.Vaccine.objects.get") as mock_get, \
             patch(f"{SERVICE}.Vaccine.objects.all", return_value=catalog_vaccines), \
             patch(f"{SERVICE}.Event.objects.filter", return_value=[make_event(days_ago=90)]):
            mock_get.return_value = MagicMock(name="Rabies")
            _, suggestions = analyze_pet_vaccines(PET_ID)
        return [
            suggestion
            for suggestion in suggestions
            if "Missing" in suggestion["title"]
            or "Upcoming" in suggestion["title"]
            or "Recommended" in suggestion["title"]
        ]

    def test_missing_vaccine_pet_old_enough_returns_warning(self):
        catalog = [make_catalog_vaccine("v_catalog_1", "Distemper", interval_days=180)]
        suggestions = self._run([], catalog, birth_date=date.today() - timedelta(days=365))
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "warning")

    def test_missing_vaccine_pet_too_young_returns_info(self):
        catalog = [make_catalog_vaccine("v_catalog_1", "Distemper", interval_days=180)]
        suggestions = self._run([], catalog, birth_date=date.today() - timedelta(days=30))
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "info")

    def test_missing_vaccine_no_birth_date_returns_generic_info(self):
        catalog = [make_catalog_vaccine("v_catalog_1", "Distemper", interval_days=180)]
        suggestions = self._run([], catalog, birth_date=None)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "info")
        self.assertIn("Recommended", suggestions[0]["title"])

    def test_already_applied_vaccine_not_suggested_as_missing(self):
        catalog = [make_catalog_vaccine("v_catalog_1", "Distemper", interval_days=180)]
        suggestions = self._run([make_vaccination(vaccine_id="v_catalog_1", days_offset=60)], catalog)
        self.assertEqual(len(suggestions), 0)

    def test_multiple_missing_vaccines_all_suggested(self):
        catalog = [
            make_catalog_vaccine("v1", "Distemper", interval_days=180),
            make_catalog_vaccine("v2", "Parvovirus", interval_days=365),
        ]
        suggestions = self._run([], catalog, birth_date=date.today() - timedelta(days=400))
        self.assertEqual(len(suggestions), 2)


class TestAnalyzeVetVisitRecency(TestCase):
    def _run(self, events):
        pet = make_pet([])
        with patch(f"{SERVICE}.Pet.objects.get", return_value=pet), \
             patch(f"{SERVICE}.Vaccine.objects.all", return_value=[]), \
             patch(f"{SERVICE}.Event.objects.filter", return_value=events):
            _, suggestions = analyze_pet_vaccines(PET_ID)
        return suggestions

    def _find_vet_alert(self, suggestions):
        for suggestion in suggestions:
            if suggestion["title"] == "No vet visit recorded yet":
                return suggestion
            if suggestion["title"] == "Time for a new vet checkup":
                return suggestion
        return None

    def test_vet_visit_older_than_180_days_returns_warning(self):
        suggestions = self._run([make_event(event_type="vet_visit", days_ago=200)])
        alert = self._find_vet_alert(suggestions)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "warning")
        self.assertIn("200", alert["message"])

    def test_vet_visit_within_180_days_returns_no_vet_alert(self):
        suggestions = self._run([make_event(event_type="vet_visit", days_ago=90)])
        alert = self._find_vet_alert(suggestions)
        self.assertIsNone(alert)

    def test_missing_vet_visit_history_returns_info(self):
        suggestions = self._run([])
        alert = self._find_vet_alert(suggestions)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "info")

    def test_legacy_check_title_counts_as_vet_visit(self):
        suggestions = self._run([make_event(title="Annual check", event_type="general", days_ago=210)])
        alert = self._find_vet_alert(suggestions)
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "warning")

    def test_most_recent_relevant_event_is_used(self):
        suggestions = self._run([
            make_event(event_type="vet_visit", days_ago=250),
            make_event(event_type="vet_visit", days_ago=40),
        ])
        alert = self._find_vet_alert(suggestions)
        self.assertIsNone(alert)


class TestSmartVaccinationView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_smart_view_requires_authentication(self):
        request = self.factory.get(f"/api/pets/{PET_ID}/smart/")
        response = pet_smart_view(request, pet_id=PET_ID)
        self.assertEqual(response.status_code, 401)

    @patch("api.views.smart_vaccination_view.analyze_pet_vaccines")
    @patch("api.authentication.firebase_authentication.auth")
    def test_smart_view_returns_data_for_owner(self, mock_auth, mock_analyze):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_user.pets = [ObjectId(PET_ID)]
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}

        pet = MagicMock(spec=Pet)
        pet.id = PET_ID
        pet.name = "Luna"
        mock_analyze.return_value = (
            pet,
            [{"type": "info", "title": "No vet visit recorded yet", "message": "x"}],
        )

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            request = _auth_request(self.factory, f"/api/pets/{PET_ID}/smart/")
            response = pet_smart_view(request, pet_id=PET_ID)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["petId"], PET_ID)
        self.assertEqual(len(data["suggestions"]), 1)

    @patch("api.views.smart_vaccination_view.analyze_pet_vaccines")
    @patch("api.authentication.firebase_authentication.auth")
    def test_smart_view_rejects_non_owner(self, mock_auth, mock_analyze):
        mock_user = MagicMock(spec=User)
        mock_user.firebase_uid = "uid123"
        mock_user.pets = [str(ObjectId())]
        mock_auth.verify_id_token.return_value = {"uid": "uid123"}
        mock_analyze.return_value = (make_pet([]), [])

        with patch("api.authentication.firebase_authentication.User") as MockUser:
            MockUser.objects.get.return_value = mock_user
            request = _auth_request(self.factory, f"/api/pets/{PET_ID}/smart/")
            response = pet_smart_view(request, pet_id=PET_ID)

        self.assertEqual(response.status_code, 403)
