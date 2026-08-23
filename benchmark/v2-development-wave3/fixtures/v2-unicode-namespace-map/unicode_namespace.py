class UnicodeNamespace:
    def __init__(self):
        self._items = {}

    def register(self, name, value):
        key = name.lower()
        if key in self._items:
            raise ValueError("duplicate")
        self._items[key] = (name, value)

    def lookup(self, name):
        return self._items[name.lower()][1]

    def display_name(self, name):
        return self._items[name.lower()][0]
