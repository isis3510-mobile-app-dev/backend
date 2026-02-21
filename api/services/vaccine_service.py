# CRUD logic for Vaccine
from api.models import Vaccine

def create_vaccine(data):
    return Vaccine.objects.create(**data)

def get_vaccine(vaccine_id):
    return Vaccine.objects.get(id=vaccine_id)

def update_vaccine(vaccine_id, data):
    Vaccine.objects.filter(id=vaccine_id).update(**data)
    return get_vaccine(vaccine_id)

def delete_vaccine(vaccine_id):
    Vaccine.objects.filter(id=vaccine_id).delete()