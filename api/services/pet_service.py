# CRUD logic for Pet
from api.models import Pet, Event, Notification, Vaccination, AttachedDocument
from datetime import datetime

def parse_payload_dates(data):
    """
    Recorre el JSON que llega de la app móvil y convierte los textos a fechas reales
    para que MongoDB los guarde correctamente como ISODate.
    """
    date_fields = [
        'birth_date', 'date_given', 'next_due_date', 
        'date', 'follow_up_date', 'date_sent', 'date_clicked'
    ]
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key in date_fields and value is not None and isinstance(value, str):
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass 
            else:
                parse_payload_dates(value)
    elif isinstance(data, list):
        for item in data:
            parse_payload_dates(item)
            
    return data

def create_pet(data):
    data = parse_payload_dates(data)
    pet = Pet.objects.create(**data)
    
    # se conviertan en objetos EmbeddedModel (Vaccination, Event, etc.)
    return Pet.objects.get(id=pet.id)

def list_pets():
    return Pet.objects.all()

def get_pet(pet_id):
    return Pet.objects.get(id=pet_id)

def update_pet(pet_id, data):
    data = parse_payload_dates(data)
    pet = Pet.objects.get(id=pet_id)
    for key, value in data.items():
        setattr(pet, key, value)
    pet.save()
    return Pet.objects.get(id=pet.id)

def delete_pet(pet_id):
    Pet.objects.filter(id=pet_id).delete()

def add_vaccination(pet_id, data):
    data = parse_payload_dates(data)
    pet = Pet.objects.get(id=pet_id)
    
    # Seguridad: Si el arreglo está en None, lo inicializamos
    if pet.vaccinations is None:
        pet.vaccinations = []
        
    pet.vaccinations.append(data)
    pet.save()
    return Pet.objects.get(id=pet.id)

def add_event(pet_id, data):
    data = parse_payload_dates(data)
    pet = Pet.objects.get(id=pet_id)
    
    if pet.events is None:
        pet.events = []
        
    pet.events.append(data)
    pet.save()
    return Pet.objects.get(id=pet.id)

def add_notification(pet_id, data):
    data = parse_payload_dates(data)
    pet = Pet.objects.get(id=pet_id)
    
    if pet.notifications is None:
        pet.notifications = []
        
    pet.notifications.append(data)
    pet.save()
    return Pet.objects.get(id=pet.id)

def add_document_to_vaccination(pet_id, vaccination_id, document_data):
    data = parse_payload_dates(document_data)
    pet = Pet.objects.get(id=pet_id)
    
    for vaccination in (pet.vaccinations or []):
        if vaccination.vaccine_id == vaccination_id:
            if vaccination.attached_documents is None:
                vaccination.attached_documents = []
            vaccination.attached_documents.append(data)
            break
            
    pet.save()
    return Pet.objects.get(id=pet.id)

def add_document_to_event(pet_id, event_id, document_data):
    data = parse_payload_dates(document_data)
    pet = Pet.objects.get(id=pet_id)
    
    for event in (pet.events or []):
        if event.event_id == event_id:
            if event.attached_documents is None:
                event.attached_documents = []
            event.attached_documents.append(data)
            break
            
    pet.save()
    return Pet.objects.get(id=pet.id)