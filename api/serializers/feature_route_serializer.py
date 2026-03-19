def feature_route_to_dict(route):
    return {
        "id": str(route.id),
        "schema": route.schema,
        "name": route.name,
        "originButton": route.originButton,
        "originScreen": route.originScreen,
        "endButton": route.endButton,
        "endScreen": route.endScreen,
        "appType": route.appType,
    }
