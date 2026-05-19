# Helper function para manejar fechas de forma segura
def notification_to_dict(notification):
    """Serialize Notification model to dictionary."""
    if not notification:
        return None

    def format_date(d):
        if not d:
            return None
        return d.isoformat() if hasattr(d, "isoformat") else str(d)

    return {
        "id": str(notification.id),
        "schema": getattr(notification, "schema", 1),
        "userId": str(notification.user_id),
        "type": notification.type,
        "header": notification.header,
        "text": notification.text,
        "actionLabel": getattr(notification, "action_label", ""),
        "actionPhone": getattr(notification, "action_phone", ""),
        "actionWhatsapp": getattr(notification, "action_whatsapp", ""),
        "actionReportId": getattr(notification, "action_report_id", ""),
        "actionPetId": getattr(notification, "action_pet_id", ""),
        "actionPetName": getattr(notification, "action_pet_name", ""),
        "actionPetPhotoUrl": getattr(notification, "action_pet_photo_url", ""),
        "actionReporterName": getattr(notification, "action_reporter_name", ""),
        "actionLocation": getattr(notification, "action_location", ""),
        "actionLatitude": getattr(notification, "action_latitude", None),
        "actionLongitude": getattr(notification, "action_longitude", None),
        "dateSent": format_date(notification.date_sent),
        "dateClicked": format_date(notification.date_clicked),
        "isRead": notification.is_read,
        "isDismissed": getattr(notification, "is_dismissed", False),
        "dateDismissed": format_date(getattr(notification, "date_dismissed", None)),
    }
