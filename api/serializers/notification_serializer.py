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
        "dateSent": format_date(notification.date_sent),
        "dateClicked": format_date(notification.date_clicked),
        "isRead": notification.is_read,
    }
