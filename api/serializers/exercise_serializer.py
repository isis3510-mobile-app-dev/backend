from datetime import timezone


def format_date(value):
    if not value:
        return None
    if hasattr(value, "isoformat"):
        if getattr(value, "tzinfo", None) is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def exercise_to_dict(exercise):
    if not exercise:
        return None

    return {
        "id": str(exercise.id),
        "schema": getattr(exercise, "schema", 1),
        "petId": str(exercise.pet_id),
        "ownerId": str(exercise.owner_id),
        "type": exercise.type,
        "startedAt": format_date(exercise.started_at),
        "durationMinutes": exercise.duration_minutes,
        "intensity": exercise.intensity,
        "distanceKm": exercise.distance_km,
        "notes": exercise.notes,
        "createdAt": format_date(exercise.created_at),
        "updatedAt": format_date(exercise.updated_at),
    }


def exercise_goal_to_dict(pet_id, goal):
    return {
        "petId": str(pet_id),
        "weeklyGoalMinutes": goal.weekly_goal_minutes if goal else 150,
    }


def exercise_route_to_dict(pet_id, exercise_id, route):
    return {
        "petId": str(pet_id),
        "exerciseId": str(exercise_id),
        "points": route.points if route else [],
    }
