class ShutdownStack:
    def __init__(self):
        self._callbacks = []
        self._closed = False

    def push(self, callback, *args, **kwargs):
        if self._closed:
            raise RuntimeError("closed")
        self._callbacks.append((callback, args, kwargs))
        return callback

    def close(self):
        if self._closed:
            return
        self._closed = True
        for callback, args, kwargs in reversed(self._callbacks):
            callback(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
