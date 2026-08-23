class AsyncResourceCoordinator:
    def __init__(self, factory, closer, limit=1):
        self.factory, self.closer, self.limit = factory, closer, limit
        self.resources = {}

    async def acquire(self, key):
        if key not in self.resources:
            self.resources[key] = [await self.factory(key), 0]
        self.resources[key][1] += 1
        return self.resources[key][0]

    async def release(self, key):
        resource, count = self.resources[key]
        if count == 1:
            await self.closer(resource)
            del self.resources[key]
        else:
            self.resources[key][1] -= 1
