def decode_event(payload):
    kind = payload["kind"]
    if kind == "created":
        return {"kind": kind, "id": payload["id"], "data": payload.get("data", {})}
    if kind == "updated":
        return {"kind": kind, "id": payload["id"], "changes": payload.get("changes", {})}
    if kind == "deleted":
        return {"kind": kind, "id": payload["id"]}
    raise ValueError("unknown kind")
