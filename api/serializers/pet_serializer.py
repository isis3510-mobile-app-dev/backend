# Helper function para manejar fechas de forma segura
def format_date(date_val):
    if not date_val:
        return None
    # Si es un objeto de fecha nativo de Python, lo formateamos
    if hasattr(date_val, 'isoformat'):
        return date_val.isoformat()
    # Si ya es un string (como cuando recién se crea desde JSON), lo devolvemos tal cual
    return str(date_val)

def pet_to_dict(pet):
    return {
        "id": str(pet.id),
        "user_ids": [str(user_id) for user_id in (pet.user_ids or [])],
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "gender": pet.gender,
        # Usamos el helper para la fecha de nacimiento
        "birth_date": format_date(pet.birth_date),
        "weight": float(pet.weight) if pet.weight else None,
        "color": pet.color,
        "photo_url": pet.photo_url,
        "status": pet.status,
        "is_nfc_synced": getattr(pet, 'is_nfc_synced', False), # Manejo seguro por si el nombre cambia
        "known_allergies": pet.known_allergies,
        "default_vet": pet.default_vet,
        "default_clinic": pet.default_clinic,
        "vaccinations": [
            {
                "vaccine_id": v.vaccine_id,
                # Usamos el helper para las fechas de las vacunas
                "date_given": format_date(v.date_given),
                "next_due_date": format_date(v.next_due_date),
                "lot_number": v.lot_number,
                "status": v.status,
                "administered_by": v.administered_by,
                "attached_documents": [
                    {
                        "document_id": doc.document_id,
                        "file_name": doc.file_name,
                        "file_uri": doc.file_uri
                    }
                    for doc in (getattr(v, 'attached_documents', []))
                ]
            }
            for v in (pet.vaccinations or [])
        ],
        "events": [
            {
                "event_id": e.event_id,
                "title": e.title,
                "event_type": e.event_type,
                # Usamos el helper para las fechas de eventos
                "date": format_date(e.date),
                "price": float(e.price) if e.price else None,
                "provider": e.provider,
                "clinic": getattr(e, 'clinic', ''),
                "description": e.description,
                "follow_up_date": format_date(e.follow_up_date),
                "attached_documents": [
                    {
                        "document_id": doc.document_id,
                        "file_name": doc.file_name,
                        "file_uri": doc.file_uri
                    }
                    for doc in (getattr(e, 'attached_documents', []))
                ]
            }
            for e in (pet.events or [])
        ],
        "notifications": [
            {
                "notification_id": n.notification_id,
                "type": n.type,
                "header": n.header,
                "text": n.text,
                # Usamos el helper para las fechas de notificaciones
                "date_sent": format_date(n.date_sent),
                "date_clicked": format_date(n.date_clicked)
            }
            for n in (pet.notifications or [])
        ]
    }