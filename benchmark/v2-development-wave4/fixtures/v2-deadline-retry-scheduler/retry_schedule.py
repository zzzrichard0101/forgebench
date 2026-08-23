def build_retry_schedule(start_ms, deadline_ms, delays_ms):
    result, current = [], start_ms
    for delay in delays_ms:
        current += delay
        if current <= deadline_ms:
            result.append(current)
    return result
