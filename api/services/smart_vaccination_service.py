from datetime import date
from api.models import Pet, Vaccine


def analyze_pet_vaccines(pet_id: str) -> tuple[Pet, list[dict]]:
    pet = Pet.objects.get(id=pet_id)
    suggestions = []
    today = date.today()

    
    applied_vaccine_ids = {
        str(v.vaccine_id) for v in pet.vaccinations
    }

    for vaccination in pet.vaccinations:
        vaccine_name = _resolve_vaccine_name(vaccination.vaccine_id)

        if not vaccination.next_due_date:
            continue

        overdue_days = (today - vaccination.next_due_date).days

        if overdue_days > 30:
            suggestions.append({
                "type": "danger",
                "title": f"Vaccine '{vaccine_name}' overdue",
                "message": f"Overdue by {overdue_days} days. Schedule an appointment soon.",
            })

        elif 0 < overdue_days <= 30:
            suggestions.append({
                "type": "warning",
                "title": f"Vaccine '{vaccine_name}' recently expired",
                "message": f"Expired {overdue_days} days ago. You still have time to catch up.",
            })

        elif -30 <= overdue_days <= 0:
            days_left = abs(overdue_days)
            suggestions.append({
                "type": "info",
                "title": f"Vaccine '{vaccine_name}' due soon",
                "message": f"Due in {days_left} days. Consider scheduling in advance.",
            })

    pet_age_days = _get_age_in_days(pet.birth_date)
    missing_suggestions = _analyze_missing_vaccines(
        species=pet.species,
        applied_vaccine_ids=applied_vaccine_ids,
        pet_age_days=pet_age_days,
    )
    suggestions.extend(missing_suggestions)

    return pet, suggestions


def _analyze_missing_vaccines(
    species: str,
    applied_vaccine_ids: set,
    pet_age_days: int | None,
) -> list[dict]:
    suggestions = []

    catalog_vaccines = [v for v in Vaccine.objects.all() if species.lower() in [s.lower() for s in v.species]]

    for vaccine in catalog_vaccines:
        vaccine_id_str = str(vaccine.id)

        if vaccine_id_str in applied_vaccine_ids:
            continue

        if pet_age_days is not None and vaccine.interval_days > 0:
            if pet_age_days >= vaccine.interval_days:
                suggestions.append({
                    "type": "warning",
                    "title": f"Missing vaccine: '{vaccine.name}'",
                    "message": (
                        f"Your pet is old enough to have received '{vaccine.name}' "
                        f"({vaccine.product_name}). It has never been recorded. "
                        f"Recommended every {vaccine.interval_days} days."
                    ),
                })
            else:
                days_until_due = vaccine.interval_days - pet_age_days
                suggestions.append({
                    "type": "info",
                    "title": f"Upcoming vaccine: '{vaccine.name}'",
                    "message": (
                        f"'{vaccine.name}' ({vaccine.product_name}) will be due "
                        f"in approximately {days_until_due} days based on your pet's age."
                    ),
                })
        else:
            suggestions.append({
                "type": "info",
                "title": f"Recommended vaccine: '{vaccine.name}'",
                "message": (
                    f"'{vaccine.name}' ({vaccine.product_name}) is recommended "
                    f"for {species}s but has never been recorded for your pet."
                ),
            })

    return suggestions


def _get_age_in_days(birth_date) -> int | None:
    if not birth_date:
        return None
    return (date.today() - birth_date).days


def _resolve_vaccine_name(vaccine_id) -> str:
    try:
        return Vaccine.objects.get(id=vaccine_id).name
    except Vaccine.DoesNotExist:
        return str(vaccine_id)