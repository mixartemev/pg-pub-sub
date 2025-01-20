import structlog
import asyncio
from asyncio import Queue
from typing_extensions import AsyncIterable
from sse_starlette.event import ServerSentEvent
from collections import defaultdict

logger = structlog.get_logger(__name__)


class Stream:
    def __init__(self) -> None:
        self._queues_by_user: dict[int, Queue] = defaultdict(Queue)

    def __call__(self, uid: int) -> AsyncIterable:
        async def _stream(user_id: int):
            while True:
                logger.info('getting item from a user queue', user_id=user_id, queues=self._queues_by_user)

                item = await self._queues_by_user[user_id].get()
                yield item
                await asyncio.sleep(0)

        return _stream(uid)

    async def asend(
        self,
        user_id: str | int,
        value: ServerSentEvent,
    ) -> None:
        logger.info('pushed an event into app stream', user_id=user_id, value=str(value))
        await self._queues_by_user[user_id].put(value)


app_stream = Stream()
