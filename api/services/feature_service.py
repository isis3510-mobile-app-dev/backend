from api.models import Feature


def create_feature(data):
    return Feature.objects.create(**data)


def get_feature(feature_id):
    return Feature.objects.get(id=feature_id)


def list_features(app_type=None):
    queryset = Feature.objects.all()
    if app_type:
        queryset = queryset.filter(appType=app_type)
    return queryset


def update_feature(feature_id, data):
    feature = Feature.objects.get(id=feature_id)
    for key, value in data.items():
        setattr(feature, key, value)
    feature.save()
    return feature


def delete_feature(feature_id):
    Feature.objects.filter(id=feature_id).delete()
