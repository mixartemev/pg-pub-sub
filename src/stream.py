from asyncio import Queue
from sse_starlette.event import ServerSentEvent


class Stream:
    def __init__(self) -> None:
        self._queue = Queue[ServerSentEvent]()

    def __aiter__(self) -> "Stream":
        return self

    async def __anext__(self) -> ServerSentEvent:
        return await self._queue.get()

    async def asend(self, value: ServerSentEvent) -> None:
        await self._queue.put(value)


stream = Stream()
