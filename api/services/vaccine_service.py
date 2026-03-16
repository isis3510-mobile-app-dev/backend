# CRUD logic for Vaccine
from api.models import Vaccine

# Mapping of camelCase API payload keys → snake_case model field names
_CAMEL_TO_SNAKE = {
    "productName": "product_name",
    "intervalDays": "interval_days",
}


def translate_payload(data):
    """Translate camelCase API payload keys to snake_case model field names."""
    if isinstance(data, dict):
        return {_CAMEL_TO_SNAKE.get(k, k): data[k] for k in data}
    return data


def create_vaccine(data):
    data = translate_payload(data)
    # Validate required fields (snake_case after translation)
    required_fields = ['schema', 'name', 'species', 'product_name', 'manufacturer', 'interval_days', 'description']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate species is a list
    if not isinstance(data.get('species'), list):
        raise ValueError("Species must be an array of strings")

    return Vaccine.objects.create(**data)


def get_vaccine(vaccine_id):
    return Vaccine.objects.get(id=vaccine_id)


def get_all_vaccines():
    return Vaccine.objects.all()


def update_vaccine(vaccine_id, data):
    data = translate_payload(data)
    vaccine = Vaccine.objects.get(id=vaccine_id)

    # Validate species if provided
    if 'species' in data and not isinstance(data['species'], list):
        raise ValueError("Species must be an array of strings")

    for key, value in data.items():
        if hasattr(vaccine, key):
            setattr(vaccine, key, value)
    vaccine.save()
    return vaccine


def delete_vaccine(vaccine_id):
    Vaccine.objects.filter(id=vaccine_id).delete()