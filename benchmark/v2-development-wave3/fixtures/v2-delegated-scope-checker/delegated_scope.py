class DelegatedScopeChecker:
    def __init__(self, policy):
        self.policy = policy

    def authorize(self, subject, delegates, action, resource):
        principal = delegates[-1] if delegates else subject
        record = self.policy.get(principal, {})
        return any(scope == f"{action}:{resource}" for scope in record.get("allow", []))
