def feature_to_dict(feature):
    return {
        "id": str(feature.id),
        "schema": feature.schema,
        "name": feature.name,
        "originButton": feature.originButton,
        "originScreen": feature.originScreen,
        "appType": feature.appType,
    }
