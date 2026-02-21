# CRUD logic for User
from api.models import User

def create_user(data):
    return User.objects.create(**data)

def get_user(user_id):
    return User.objects.get(id=user_id)

def update_user(user_id, data):
    User.objects.filter(id=user_id).update(**data)
    return get_user(user_id)

def delete_user(user_id):
    User.objects.filter(id=user_id).delete()

