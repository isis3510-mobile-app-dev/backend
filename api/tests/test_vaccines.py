import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from bson import ObjectId

from api.views.vaccine_views import (
    create_vaccine_view,
    get_vaccine_view,
    update_vaccine_view,
    delete_vaccine_view,
    list_vaccines_view,
)
from api.models import Vaccine
from api.services import vaccine_service
from api.serializers.vaccine_serializer import vaccine_to_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VACCINE_ID = str(ObjectId())


def _make_vaccine(**kwargs):
    """Create a mock Vaccine using snake_case model attribute names."""
    v = MagicMock(spec=Vaccine)
    v.id = ObjectId(VACCINE_ID)
    v.schema = kwargs.get("schema", 1)
    v.name = kwargs.get("name", "Rabies")
    v.species = kwargs.get("species", ["dog", "cat"])
    v.product_name = kwargs.get("product_name", "Nobivac Rabies")
    v.manufacturer = kwargs.get("manufacturer", "MSD")
    v.interval_days = kwargs.get("interval_days", 365)
    v.description = kwargs.get("description", "Anti-rabies vaccine")
    return v


# ===========================================================================
# Vaccine Service Tests
# ===========================================================================

class TestVaccineService(TestCase):

    @patch("api.services.vaccine_service.Vaccine")
    def test_create_vaccine_ok(self, MockVaccine):
        created = _make_vaccine(name="Distemper")
        MockVaccine.objects.create.return_value = created
        # API sends camelCase; service translates to snake_case before ORM
        data = {
            "schema": 1,
            "name": "Distemper",
            "species": ["dog"],
            "productName": "Nobivac DHPPi",
            "manufacturer": "MSD",
            "intervalDays": 365,
            "description": "Distemper combo vaccine",
        }
        result = vaccine_service.create_vaccine(data)
        self.assertEqual(result.name, "Distemper")
        MockVaccine.objects.create.assert_called_once()

    def test_create_vaccine_missing_field_raises(self):
        data = {"name": "Rabies"}  # missing required fields
        with self.assertRaises(ValueError):
            vaccine_service.create_vaccine(data)

    def test_create_vaccine_species_not_list_raises(self):
        data = {
            "schema": 1,
            "name": "Rabies",
            "species": "dog",  # should be a list
            "productName": "Nobivac",
            "manufacturer": "MSD",
            "intervalDays": 365,
            "description": "desc",
        }
        with self.assertRaises(ValueError):
            vaccine_service.create_vaccine(data)

    @patch("api.services.vaccine_service.Vaccine")
    def test_get_vaccine_found(self, MockVaccine):
        expected = _make_vaccine()
        MockVaccine.objects.get.return_value = expected
        result = vaccine_service.get_vaccine(VACCINE_ID)
        self.assertEqual(result, expected)
        MockVaccine.objects.get.assert_called_once_with(id=VACCINE_ID)

    @patch("api.services.vaccine_service.Vaccine")
    def test_get_vaccine_not_found_raises(self, MockVaccine):
        MockVaccine.DoesNotExist = Vaccine.DoesNotExist
        MockVaccine.objects.get.side_effect = Vaccine.DoesNotExist
        with self.assertRaises(Vaccine.DoesNotExist):
            vaccine_service.get_vaccine("bad_id")

    @patch("api.services.vaccine_service.Vaccine")
    def test_get_all_vaccines(self, MockVaccine):
        MockVaccine.objects.all.return_value = [_make_vaccine(), _make_vaccine(name="Distemper")]
        result = vaccine_service.get_all_vaccines()
        self.assertEqual(len(result), 2)
        MockVaccine.objects.all.assert_called_once()

    @patch("api.services.vaccine_service.Vaccine")
    def test_update_vaccine_ok(self, MockVaccine):
        vaccine = _make_vaccine(name="Old")
        MockVaccine.objects.get.return_value = vaccine
        # API sends camelCase; service translates
        result = vaccine_service.update_vaccine(VACCINE_ID, {"name": "New"})
        vaccine.save.assert_called_once()
        self.assertEqual(result, vaccine)

    @patch("api.services.vaccine_service.Vaccine")
    def test_update_vaccine_not_found(self, MockVaccine):
        MockVaccine.DoesNotExist = Vaccine.DoesNotExist
        MockVaccine.objects.get.side_effect = Vaccine.DoesNotExist
        with self.assertRaises(Vaccine.DoesNotExist):
            vaccine_service.update_vaccine("bad_id", {"name": "X"})

    def test_update_vaccine_species_not_list_raises(self):
        with patch("api.services.vaccine_service.Vaccine") as MockVaccine:
            vaccine = _make_vaccine()
            MockVaccine.objects.get.return_value = vaccine
            with self.assertRaises(ValueError):
                vaccine_service.update_vaccine(VACCINE_ID, {"species": "dog"})

    @patch("api.services.vaccine_service.Vaccine")
    def test_delete_vaccine(self, MockVaccine):
        MockVaccine.objects.filter.return_value.delete.return_value = None
        vaccine_service.delete_vaccine(VACCINE_ID)
        MockVaccine.objects.filter.assert_called_once_with(id=VACCINE_ID)
        MockVaccine.objects.filter.return_value.delete.assert_called_once()


# ===========================================================================
# Vaccine View Tests
# ===========================================================================

class TestVaccineViews(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    # --- POST /api/vaccines/create/ ---

    @patch("api.views.vaccine_views.create_vaccine")
    def test_create_vaccine_view_ok(self, mock_create):
        mock_create.return_value = _make_vaccine(name="Rabies")
        # Request body uses camelCase (API contract)
        payload = {
            "schema": 1,
            "name": "Rabies",
            "species": ["dog", "cat"],
            "productName": "Nobivac Rabies",
            "manufacturer": "MSD",
            "intervalDays": 365,
            "description": "Anti-rabies vaccine",
        }
        req = self.factory.post(
            "/api/vaccines/create/",
            json.dumps(payload),
            content_type="application/json",
        )
        resp = create_vaccine_view(req)
        self.assertEqual(resp.status_code, 201)
        data = json.loads(resp.content)
        self.assertEqual(data["name"], "Rabies")
        self.assertEqual(data["species"], ["dog", "cat"])

    @patch("api.views.vaccine_views.create_vaccine")
    def test_create_vaccine_view_missing_field(self, mock_create):
        mock_create.side_effect = ValueError("Missing required field: product_name")
        payload = {"name": "Rabies"}
        req = self.factory.post(
            "/api/vaccines/create/",
            json.dumps(payload),
            content_type="application/json",
        )
        resp = create_vaccine_view(req)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", json.loads(resp.content))

    @patch("api.views.vaccine_views.create_vaccine")
    def test_create_vaccine_view_service_error(self, mock_create):
        mock_create.side_effect = Exception("DB error")
        req = self.factory.post(
            "/api/vaccines/create/",
            json.dumps({"name": "X"}),
            content_type="application/json",
        )
        resp = create_vaccine_view(req)
        self.assertEqual(resp.status_code, 400)

    # --- GET /api/vaccines/<id>/ ---

    @patch("api.views.vaccine_views.get_vaccine")
    def test_get_vaccine_view_ok(self, mock_get):
        mock_get.return_value = _make_vaccine()
        req = self.factory.get(f"/api/vaccines/{VACCINE_ID}/")
        resp = get_vaccine_view(req, vaccine_id=VACCINE_ID)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["id"], VACCINE_ID)
        self.assertEqual(data["name"], "Rabies")
        # Response uses camelCase keys
        self.assertEqual(data["productName"], "Nobivac Rabies")
        self.assertEqual(data["intervalDays"], 365)

    @patch("api.views.vaccine_views.get_vaccine")
    def test_get_vaccine_view_not_found(self, mock_get):
        mock_get.side_effect = Vaccine.DoesNotExist
        req = self.factory.get("/api/vaccines/badid/")
        resp = get_vaccine_view(req, vaccine_id="badid")
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Vaccine not found", json.loads(resp.content)["error"])

    # --- PUT /api/vaccines/<id>/update/ ---

    @patch("api.views.vaccine_views.update_vaccine")
    def test_update_vaccine_view_ok(self, mock_update):
        mock_update.return_value = _make_vaccine(name="Updated")
        req = self.factory.put(
            f"/api/vaccines/{VACCINE_ID}/update/",
            json.dumps({"name": "Updated"}),
            content_type="application/json",
        )
        resp = update_vaccine_view(req, vaccine_id=VACCINE_ID)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content)["name"], "Updated")

    @patch("api.views.vaccine_views.update_vaccine")
    def test_update_vaccine_view_not_found(self, mock_update):
        mock_update.side_effect = Vaccine.DoesNotExist
        req = self.factory.put(
            "/api/vaccines/badid/update/",
            json.dumps({"name": "X"}),
            content_type="application/json",
        )
        resp = update_vaccine_view(req, vaccine_id="badid")
        self.assertEqual(resp.status_code, 404)

    @patch("api.views.vaccine_views.update_vaccine")
    def test_update_vaccine_view_invalid_json(self, mock_update):
        req = self.factory.put(
            f"/api/vaccines/{VACCINE_ID}/update/",
            "not-json",
            content_type="application/json",
        )
        resp = update_vaccine_view(req, vaccine_id=VACCINE_ID)
        self.assertEqual(resp.status_code, 400)

    @patch("api.views.vaccine_views.update_vaccine")
    def test_update_vaccine_view_validation_error(self, mock_update):
        mock_update.side_effect = ValueError("Species must be an array of strings")
        req = self.factory.put(
            f"/api/vaccines/{VACCINE_ID}/update/",
            json.dumps({"species": "dog"}),  # should be a list
            content_type="application/json",
        )
        resp = update_vaccine_view(req, vaccine_id=VACCINE_ID)
        self.assertEqual(resp.status_code, 400)

    # --- DELETE /api/vaccines/<id>/delete/ ---

    @patch("api.views.vaccine_views.delete_vaccine")
    def test_delete_vaccine_view_ok(self, mock_delete):
        mock_delete.return_value = None
        req = self.factory.delete(f"/api/vaccines/{VACCINE_ID}/delete/")
        resp = delete_vaccine_view(req, vaccine_id=VACCINE_ID)
        self.assertEqual(resp.status_code, 204)

    @patch("api.views.vaccine_views.delete_vaccine")
    def test_delete_vaccine_view_not_found(self, mock_delete):
        mock_delete.side_effect = Vaccine.DoesNotExist
        req = self.factory.delete("/api/vaccines/badid/delete/")
        resp = delete_vaccine_view(req, vaccine_id="badid")
        self.assertEqual(resp.status_code, 404)

    # --- GET /api/vaccines/ ---

    @patch("api.views.vaccine_views.get_all_vaccines")
    def test_list_vaccines_view_ok(self, mock_list):
        mock_list.return_value = [_make_vaccine(), _make_vaccine(name="Distemper")]
        req = self.factory.get("/api/vaccines/")
        resp = list_vaccines_view(req)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    @patch("api.views.vaccine_views.get_all_vaccines")
    def test_list_vaccines_view_empty(self, mock_list):
        mock_list.return_value = []
        req = self.factory.get("/api/vaccines/")
        resp = list_vaccines_view(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), [])

    @patch("api.views.vaccine_views.get_all_vaccines")
    def test_list_vaccines_view_service_error(self, mock_list):
        mock_list.side_effect = Exception("DB error")
        req = self.factory.get("/api/vaccines/")
        resp = list_vaccines_view(req)
        self.assertEqual(resp.status_code, 400)


# ===========================================================================
# Serializer Tests
# ===========================================================================

class TestVaccineSerializer(TestCase):

    def test_vaccine_to_dict_all_fields(self):
        v = _make_vaccine(
            name="Rabies",
            species=["dog", "cat"],
            product_name="Nobivac Rabies",
            manufacturer="MSD",
            interval_days=365,
            description="Anti-rabies vaccine",
        )
        result = vaccine_to_dict(v)
        self.assertEqual(result["id"], VACCINE_ID)
        self.assertEqual(result["schema"], 1)
        self.assertEqual(result["name"], "Rabies")
        self.assertEqual(result["species"], ["dog", "cat"])
        # Response JSON uses camelCase keys
        self.assertEqual(result["productName"], "Nobivac Rabies")
        self.assertEqual(result["manufacturer"], "MSD")
        self.assertEqual(result["intervalDays"], 365)
        self.assertEqual(result["description"], "Anti-rabies vaccine")

    def test_vaccine_to_dict_empty_species(self):
        v = _make_vaccine(species=[])
        result = vaccine_to_dict(v)
        self.assertEqual(result["species"], [])
