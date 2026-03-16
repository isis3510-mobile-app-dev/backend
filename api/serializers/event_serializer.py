def format_date(d):
    if not d:
        return None
    return d.isoformat() if hasattr(d, "isoformat") else str(d)


def event_to_dict(event):
    """Serialize Event model to dictionary with camelCase JSON keys."""
    if not event:
        return None

    return {
        "id": str(event.id),
        "schema": getattr(event, "schema", 1),
        "petId": str(event.pet_id),
        "ownerId": str(event.owner_id),
        "title": event.title,
        "eventType": event.event_type,
        "date": format_date(event.date),
        "price": float(event.price) if event.price is not None else None,
        "provider": event.provider,
        "clinic": event.clinic,
        "description": event.description,
        "followUpDate": format_date(event.follow_up_date),
        "attachedDocuments": [
            {
                "documentId": str(doc.document_id),
                "fileName": doc.file_name,
                "fileUri": doc.file_uri,
            }
            for doc in (event.attached_documents or [])
        ],
    }
