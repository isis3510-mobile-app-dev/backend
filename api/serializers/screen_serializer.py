# Manual serializer for Screen

def screen_to_dict(screen):
    return {
        "id": str(screen.id),
        "schema": screen.schema,
        "name": screen.name,
        "hasAds": screen.hasAds,
        # "avgTimeSpent": screen.avgTimeSpent,
        # "stdTimeSpent": screen.stdTimeSpent,
        # "nScreenTimeEvents": screen.nScreenTimeEvents,
        "buttons": [
            {
                "buttonId": b.buttonId,
                "schema": b.schema,
                "name": b.name,
            }
            for b in (screen.buttons or [])
        ],
    }
