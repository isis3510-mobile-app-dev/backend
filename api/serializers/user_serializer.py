# Manual serializer for User

def user_to_dict(user):
    return {
        "id": str(user.id),
        "firebase_uid": user.firebase_uid,
        "pet_ids": [str(pet_id) for pet_id in user.pet_ids],
        "name": user.name,
        "photo_url": user.photo_url,
        "phone": user.phone,
        "address": user.address,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }