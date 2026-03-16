# CRUD logic for Screen
from api.models import Screen


def create_screen(data):
    screen = Screen.objects.create(**data)
    # Re-fetch so embedded Button objects are properly deserialized
    return Screen.objects.get(id=screen.id)


def get_screen(screen_id):
    return Screen.objects.get(id=screen_id)


def list_screens():
    return Screen.objects.all()
