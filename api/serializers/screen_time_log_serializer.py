def screen_time_log_to_dict(log):
    return {
        "id": str(log.id),
        "schema": log.schema,
        "userId": log.userId,
        "screenId": log.screenId,
        "startTime": log.startTime.isoformat() if log.startTime else None,
        "endTime": log.endTime.isoformat() if log.endTime else None,
        "totalTime": log.totalTime,
        "appType": log.appType,
    }
