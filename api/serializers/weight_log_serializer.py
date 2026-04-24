from datetime import timezone


def _format_datetime(value):
    if not value:
        return None
    if hasattr(value, "isoformat"):
        if getattr(value, "tzinfo", None) is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def weight_log_to_dict(weight_log):
    if not weight_log:
        return None

    return {
        "id": str(weight_log.id),
        "schema": getattr(weight_log, "schema", 1),
        "petId": str(weight_log.pet_id),
        "ownerId": str(weight_log.owner_id),
        "weight": float(weight_log.weight),
        "loggedAt": _format_datetime(weight_log.logged_at),
        "clientMutationId": weight_log.client_mutation_id,
        "createdAt": _format_datetime(getattr(weight_log, "created_at", None)),
        "updatedAt": _format_datetime(getattr(weight_log, "updated_at", None)),
    }
