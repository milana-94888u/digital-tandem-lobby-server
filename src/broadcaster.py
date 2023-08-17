from typing import Any, Generator
import asyncio


class Broadcaster:
    def __init__(self) -> None:
        self._queues: set[asyncio.Queue] = set()

    async def publish(self, message: Any) -> None:
        for queue in self._queues:
            await queue.put(message)

    async def subscribe(self) -> Generator[Any, None, None]:
        queue = asyncio.Queue()
        self._queues.add(queue)

        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            self._queues.remove(queue)
