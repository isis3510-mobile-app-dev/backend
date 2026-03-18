# api/tests/test_smart_vaccination_feature.py
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from api.models import Vaccine
from api.services.smart_vaccination_service import analyze_pet_vaccines

SERVICE = "api.services.smart_vaccination_service"


def make_vaccination(vaccine_id="abc123", days_offset=None, next_due_date=None):
    v = MagicMock()
    v.vaccine_id = vaccine_id
    if next_due_date is not None:
        v.next_due_date = next_due_date
    elif days_offset is not None:
        v.next_due_date = date.today() + timedelta(days=days_offset)
    else:
        v.next_due_date = None
    return v


def make_catalog_vaccine(vaccine_id, name, interval_days=365, product_name=""):
    v = MagicMock(spec=Vaccine)
    v.id = vaccine_id
    v.name = name
    v.product_name = product_name
    v.interval_days = interval_days
    return v


def make_pet(vaccinations, species="dog", birth_date=None):
    pet = MagicMock()
    pet.id = "pet_test_id"
    pet.name = "Luna"
    pet.species = species
    pet.birth_date = birth_date
    pet.vaccinations = vaccinations
    return pet


class TestAnalyzePetVaccinesExisting(TestCase):
    """Tests for already-registered vaccinations"""

    def _run(self, vaccinations, vaccine_name="Rabies", catalog=None):
        pet = make_pet(vaccinations)
        catalog = catalog or []
        with patch(f"{SERVICE}.Pet.objects.get", return_value=pet), \
             patch(f"{SERVICE}.Vaccine.objects.get") as mock_get, \
             patch(f"{SERVICE}.Vaccine.objects.filter", return_value=catalog):
            mock_vaccine = MagicMock()
            mock_vaccine.name = vaccine_name
            mock_get.return_value = mock_vaccine
            _, suggestions = analyze_pet_vaccines("pet_test_id")
        return suggestions

    def test_vaccine_overdue_more_than_30_days_returns_danger(self):
        suggestions = self._run([make_vaccination(days_offset=-45)])
        types = [s["type"] for s in suggestions]
        self.assertIn("danger", types)
        danger = next(s for s in suggestions if s["type"] == "danger")
        self.assertIn("45", danger["message"])

    def test_vaccine_overdue_less_than_30_days_returns_warning(self):
        suggestions = self._run([make_vaccination(days_offset=-10)])
        types = [s["type"] for s in suggestions]
        self.assertIn("warning", types)

    def test_vaccine_due_within_30_days_returns_info(self):
        suggestions = self._run([make_vaccination(days_offset=15)])
        types = [s["type"] for s in suggestions]
        self.assertIn("info", types)

    def test_vaccine_not_due_soon_returns_no_suggestion(self):
        suggestions = self._run([make_vaccination(days_offset=60)])
        self.assertEqual(len(suggestions), 0)

    def test_vaccination_without_next_due_date_is_skipped(self):
        suggestions = self._run([make_vaccination(next_due_date=None)])
        self.assertEqual(len(suggestions), 0)

    def test_no_vaccinations_returns_no_suggestions(self):
        suggestions = self._run([])
        self.assertEqual(len(suggestions), 0)

    def test_vaccine_due_exactly_today_returns_info(self):
        suggestions = self._run([make_vaccination(days_offset=0)])
        types = [s["type"] for s in suggestions]
        self.assertIn("info", types)

    def test_vaccine_overdue_exactly_30_days_returns_warning(self):
        suggestions = self._run([make_vaccination(days_offset=-30)])
        types = [s["type"] for s in suggestions]
        self.assertIn("warning", types)

    def test_vaccine_overdue_exactly_31_days_returns_danger(self):
        suggestions = self._run([make_vaccination(days_offset=-31)])
        types = [s["type"] for s in suggestions]
        self.assertIn("danger", types)

    def test_unknown_vaccine_id_falls_back_to_id_string(self):
        pet = make_pet([make_vaccination(vaccine_id="unknown_id", days_offset=-45)])
        with patch(f"{SERVICE}.Pet.objects.get", return_value=pet), \
             patch(f"{SERVICE}.Vaccine.objects.get", side_effect=Vaccine.DoesNotExist), \
             patch(f"{SERVICE}.Vaccine.objects.filter", return_value=[]):
            _, suggestions = analyze_pet_vaccines("pet_test_id")
        self.assertIn("unknown_id", suggestions[0]["title"])


class TestAnalyzeMissingVaccines(TestCase):
    """Tests for missing vaccines from the catalog."""

    def _run(self, vaccinations, catalog_vaccines, species="dog", birth_date=None):
        pet = make_pet(vaccinations, species=species, birth_date=birth_date)
        with patch(f"{SERVICE}.Pet.objects.get", return_value=pet), \
             patch(f"{SERVICE}.Vaccine.objects.get") as mock_get, \
             patch(f"{SERVICE}.Vaccine.objects.filter", return_value=catalog_vaccines):
            mock_get.return_value = MagicMock(name="Rabies")
            _, suggestions = analyze_pet_vaccines("pet_test_id")
        # Return only missing-vaccine suggestions
        return [s for s in suggestions if "Missing" in s["title"] or
                "Upcoming" in s["title"] or "Recommended" in s["title"]]

    def test_missing_vaccine_pet_old_enough_returns_warning(self):
        catalog = [make_catalog_vaccine("v_catalog_1", "Distemper", interval_days=180)]
        # Pet is 365 days old 
        birth_date = date.today() - timedelta(days=365)
        suggestions = self._run([], catalog, birth_date=birth_date)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "warning")
        self.assertIn("Distemper", suggestions[0]["title"])

    def test_missing_vaccine_pet_too_young_returns_info(self):
        catalog = [make_catalog_vaccine("v_catalog_1", "Distemper", interval_days=180)]
        # Pet is 30 days old 
        birth_date = date.today() - timedelta(days=30)
        suggestions = self._run([], catalog, birth_date=birth_date)
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
        # Pet already has this vaccine applied
        vaccination = make_vaccination(vaccine_id="v_catalog_1", days_offset=60)
        suggestions = self._run([vaccination], catalog)
        self.assertEqual(len(suggestions), 0)

    def test_no_catalog_vaccines_for_species_returns_no_missing_suggestions(self):
        suggestions = self._run([], catalog_vaccines=[], birth_date=date.today() - timedelta(days=365))
        self.assertEqual(len(suggestions), 0)

    def test_multiple_missing_vaccines_all_suggested(self):
        catalog = [
            make_catalog_vaccine("v1", "Distemper", interval_days=180),
            make_catalog_vaccine("v2", "Parvovirus", interval_days=365),
        ]
        birth_date = date.today() - timedelta(days=400)
        suggestions = self._run([], catalog, birth_date=birth_date)
        self.assertEqual(len(suggestions), 2)
        self.assertTrue(all(s["type"] == "warning" for s in suggestions))