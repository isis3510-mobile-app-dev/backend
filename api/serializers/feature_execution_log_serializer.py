def feature_execution_log_to_dict(log):
    return {
        "id": str(log.id),
        "schema": log.schema,
        "userId": str(log.userId) if log.userId is not None else None,
        "featureId": str(log.featureId) if log.featureId is not None else None,
        "startTime": log.startTime.isoformat() if log.startTime else None,
        "endTime": log.endTime.isoformat() if log.endTime else None,
        "totalTime": log.totalTime,
        "downloadSpeed": log.downloadSpeed,
        "uploadSpeed": log.uploadSpeed,
        "appType": log.appType,
    }
