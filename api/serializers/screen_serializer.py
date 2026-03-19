def screen_to_dict(screen):
    return {
        "id": str(screen.id),
        "schema": screen.schema,
        "name": screen.name,
        "hasAds": screen.hasAds,
        "appType": screen.appType,
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
