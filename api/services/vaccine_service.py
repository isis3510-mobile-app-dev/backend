# CRUD logic for Vaccine
from api.models import Vaccine

def create_vaccine(data):
    # Validate required fields
    required_fields = ['schema', 'name', 'species', 'productName', 'manufacturer', 'intervalDays', 'description']
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