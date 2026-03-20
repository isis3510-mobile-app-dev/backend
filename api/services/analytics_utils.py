from bson import ObjectId
from api.models import User, Screen, Feature, FeatureRoute
import logging

logger = logging.getLogger(__name__)

def _to_object_id(val):
    if not val: return None
    if isinstance(val, ObjectId): return val
    try:
        if len(str(val)) == 24:
            return ObjectId(val)
    except:
        pass
    return None

def resolve_user_id(val):
    """If val is a firebase_uid, return the MongoDB _id."""
    if not val or val == "unknown":
        return None
    oid = _to_object_id(val)
    if oid: return oid
    
    user = User.objects.filter(firebase_uid=val).first()
    if not user:
        logger.warning(f"resolve_user_id: User with firebase_uid '{val}' not found.")
        return None
    return user.id

def resolve_screen_id(val, app_type="Kotlin"):
    if not val:
        return None
    oid = _to_object_id(val)
    if oid: return oid
    
    screen = Screen.objects.filter(name=val, appType=app_type).first()
    if not screen:
        logger.warning(f"resolve_screen_id: Screen '{val}' not found for appType '{app_type}'.")
        return None
    return screen.id

def resolve_feature_id(val, app_type="Kotlin"):
    if not val:
        return None
    oid = _to_object_id(val)
    if oid: return oid
    
    feature = Feature.objects.filter(name=val, appType=app_type).first()
    if not feature:
        logger.warning(f"resolve_feature_id: Feature '{val}' not found for appType '{app_type}'.")
        return None
    return feature.id

def resolve_route_id(val, app_type="Kotlin"):
    if not val:
        return None
    oid = _to_object_id(val)
    if oid: return oid
    
    route = FeatureRoute.objects.filter(name=val, appType=app_type).first()
    if not route:
        logger.warning(f"resolve_route_id: FeatureRoute '{val}' not found for appType '{app_type}'.")
        return None
    return route.id
