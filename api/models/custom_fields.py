"""Custom Django fields for MongoDB backend."""
from django_mongodb_backend.fields import ObjectIdField


class SafeObjectIdField(ObjectIdField):
    """Custom ObjectIdField that handles empty strings gracefully by converting them to None."""
    
    def to_python(self, value):
        # Handle empty strings by converting to None
        if isinstance(value, str) and value == "":
            return None
        # Let the parent method handle the rest
        return super().to_python(value)
