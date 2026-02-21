# Manual serializer for Pet

def pet_to_dict(pet):
    return {
        "id": str(pet.id),
        "user_ids": [str(user_id) for user_id in pet.user_ids],
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "weight": float(pet.weight) if pet.weight else None,
        "birth_date": pet.birth_date.isoformat() if pet.birth_date else None,
        "photo_url": pet.photo_url,
        "behavior_notes": pet.behavior_notes,
        "vaccination_events": [
            {
                "vaccine_name": v.vaccine_name,
                "date": v.date.isoformat(),
                "booster_number": v.booster_number,
            }
            for v in pet.vaccination_events
        ],
        "medical_history": [
            {
                "title": mh.title,
                "date": mh.date.isoformat(),
                "description": mh.description,
                "file_url": mh.file_url
            }
            for mh in pet.medical_history
        ],
    }