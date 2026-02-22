# CRUD logic for Pet
from api.models import Pet, VaccinationEvent, MedicalRecord

def create_pet(data):
    return Pet.objects.create(**data)

def list_pets():
    return Pet.objects.all()

def get_pet(pet_id):
    return Pet.objects.get(id=pet_id)

def update_pet(pet_id, data):
    Pet.objects.filter(id=pet_id).update(**data)
    return get_pet(pet_id)

def delete_pet(pet_id):
    Pet.objects.filter(id=pet_id).delete()

def add_vaccination_event(pet_id, data):
    pet = Pet.objects.filter(id=pet_id)
    pet.vaccination_events.append(data)
    pet.save()
    return pet

def add_medical_record(pet_id, data):
    pet = Pet.objects.filter(id=pet_id)
    pet.medical_history.append(data)
    pet.save()
    return pet