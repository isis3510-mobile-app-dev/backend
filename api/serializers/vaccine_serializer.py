# Manual serializer for Vaccine

def vaccine_to_dict(vaccine):
    return {
        "id": str(vaccine.id),
        "name": vaccine.name,
        "characteristics": vaccine.characteristics,
        "application_moment": vaccine.application_moment,
        "animal_type": vaccine.animal_type,
    }