# CRUD logic for Vaccine
from api.models import Vaccine

def create_vaccine(data):
    return Vaccine.objects.create(**data)

def get_vaccine(vaccine_id):
    return Vaccine.objects.get(id=vaccine_id)

def get_all_vaccines():
    return Vaccine.objects.all()

def update_vaccine(vaccine_id, data):
    vaccine = Vaccine.objects.get(id=vaccine_id)
    for key, value in data.items():
        setattr(vaccine, key, value)
    vaccine.save()
    return vaccine

def delete_vaccine(vaccine_id):
    Vaccine.objects.filter(id=vaccine_id).delete()