def suggestion_to_dict(suggestion: dict) -> dict:
    return {
        "type": suggestion["type"],       # "danger" | "warning" | "info"
        "title": suggestion["title"],
        "message": suggestion["message"],
    }

def smart_response_to_dict(pet, suggestions: list) -> dict:
    return {
        "petId": str(pet.id),
        "petName": pet.name,
        "suggestions": [suggestion_to_dict(s) for s in suggestions],
    }