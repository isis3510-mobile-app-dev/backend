# Manual serializer for Vaccine

def vaccine_to_dict(vaccine):
    return {
        "id": str(vaccine.id),
        "schema": vaccine.schema,
        "name": vaccine.name,
        "species": vaccine.species,
        "productName": vaccine.productName,
        "manufacturer": vaccine.manufacturer,
        "intervalDays": vaccine.intervalDays,
        "description": vaccine.description,
    }