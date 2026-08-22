from contextlib import contextmanager


class LeasePool:
    def __init__(self, acquire, release) -> None:
        self.acquire = acquire
        self.release = release

    @contextmanager
    def lease(self, key: str):
        resource = self.acquire(key)
        try:
            yield resource
        finally:
            self.release(resource)

