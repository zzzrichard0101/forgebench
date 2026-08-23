class DomainLabelRegistry:
    def __init__(self): self.items = {}
    def register(self, name, value): self.items[name.lower()] = (name, value)
    def lookup(self, name): return self.items[name.lower()][1]
    def ascii_name(self, name): return name.encode("idna").decode("ascii")
