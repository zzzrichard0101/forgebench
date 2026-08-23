def exchange_capability(token, requested_scopes, audience, now):
    if token["audience"] != audience or token["expires_at"] <= now:
        raise ValueError("invalid token")
    return {**token, "scopes": list(requested_scopes)}
