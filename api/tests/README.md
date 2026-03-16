# Run test for telemetry

```bash
conda activate pet_backend
python manage.py test api.tests.test_screens api.tests.test_features --settings=backend.test_settings -v2
```