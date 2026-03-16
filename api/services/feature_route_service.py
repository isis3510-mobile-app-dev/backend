from api.models import FeatureRoute


def create_feature_route(data):
    return FeatureRoute.objects.create(**data)


def get_feature_route(route_id):
    return FeatureRoute.objects.get(id=route_id)


def list_feature_routes():
    return FeatureRoute.objects.all()


def update_feature_route(route_id, data):
    route = FeatureRoute.objects.get(id=route_id)
    for key, value in data.items():
        setattr(route, key, value)
    route.save()
    return route


def delete_feature_route(route_id):
    FeatureRoute.objects.filter(id=route_id).delete()
