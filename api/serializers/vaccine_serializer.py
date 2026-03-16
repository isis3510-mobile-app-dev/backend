def vaccine_to_dict(vaccine):
    return {
        "id": str(vaccine.id),
        "schema": vaccine.schema,
        "name": vaccine.name,
        "species": vaccine.species,
        "productName": vaccine.product_name,
        "manufacturer": vaccine.manufacturer,
        "intervalDays": vaccine.interval_days,
        "description": vaccine.description,
    }