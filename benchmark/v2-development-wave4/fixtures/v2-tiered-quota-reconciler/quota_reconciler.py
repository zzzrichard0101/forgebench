def allocate_quota(total, requests, tier_caps):
    remaining = total
    allocations = {}
    for request in requests:
        amount = min(request["amount"], remaining)
        allocations[request["id"]] = amount
        remaining -= amount
    return {"allocations": allocations, "remaining": remaining}
