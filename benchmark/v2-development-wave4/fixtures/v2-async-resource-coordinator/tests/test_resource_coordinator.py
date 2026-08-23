import unittest
from resource_coordinator import AsyncResourceCoordinator

class PublicTests(unittest.IsolatedAsyncioTestCase):
    async def test_shared(self):
        async def factory(key): return {"key": key}
        async def closer(value): return None
        pool = AsyncResourceCoordinator(factory, closer, 1)
        self.assertIs(await pool.acquire("a"), await pool.acquire("a"))

if __name__ == "__main__": unittest.main()
