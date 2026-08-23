def plan_extraction(members):
    return [member["name"] for member in members if member.get("type", "file") == "file"]
