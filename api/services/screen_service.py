from api.models import Screen


def create_screen(data):
    screen = Screen.objects.create(**data)
    return Screen.objects.get(id=screen.id)


def get_screen(screen_id):
    return Screen.objects.get(id=screen_id)


def list_screens(app_type=None):
    queryset = Screen.objects.all()
    if app_type:
        queryset = queryset.filter(appType=app_type)
    return queryset


def update_screen(screen_id, data):
    screen = Screen.objects.get(id=screen_id)
    for key, value in data.items():
        setattr(screen, key, value)
    screen.save()
    return Screen.objects.get(id=screen.id)


def delete_screen(screen_id):
    Screen.objects.filter(id=screen_id).delete()

