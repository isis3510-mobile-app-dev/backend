def feature_clicks_log_to_dict(log):
    return {
        "id": str(log.id),
        "schema": log.schema,
        "userId": str(log.userId) if log.userId is not None else None,
        "routeId": str(log.routeId) if log.routeId is not None else None,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "nClicks": log.nClicks,
    }
