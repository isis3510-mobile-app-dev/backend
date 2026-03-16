def feature_clicks_log_to_dict(log):
    return {
        "id": str(log.id),
        "schema": log.schema,
        "userId": log.userId,
        "routeId": log.routeId,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "nClicks": log.nClicks,
    }
