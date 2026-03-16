# Run all API tests

```bash
conda activate pet_backend
python manage.py test api.tests.test_screens api.tests.test_features api.tests.test_vaccines api.tests.test_pets api.tests.test_users --settings=backend.test_settings -v2
```

```bash
conda activate pet_backend
python manage.py test api.tests --verbosity=2
```