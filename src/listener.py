import asyncio
import inspect
from collections import defaultdict
from typing import Any
from collections.abc import Coroutine
import functools
from pydantic import ValidationError
import asyncpg
import structlog

from src.base_model import Model


logger = structlog.get_logger(__name__)


class ListenerImproperlyConfiguredError(Exception):
    pass


class Listener:
    def __init__(self) -> None:
        # TODO add connection health check as a separate task
        self._connection = None

        self._registry = defaultdict(list)
        self._queue = asyncio.Queue()

    def set_connection(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    def subscribe(self, channel: str) -> None:
        if not channel:
            raise NotImplementedError('Please provide a proper channel to subscribe')

        def _wrapper(func: Coroutine[Model]):

            @functools.wraps(func)
            async def _async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            self._registry[channel].append(_async_wrapper)

            return _async_wrapper

        return _wrapper

    async def start(self) -> None:
        if self._connection is None:
            raise ListenerImproperlyConfiguredError('Please set a database connection')

        await self._listen_to_notifications()

        async with asyncio.TaskGroup() as tg:
            await self._process(tg)

    async def _process(self, tg: asyncio.TaskGroup) -> None:
        while True:
            channel, payload = await self._queue.get()

            consumers = self._registry.get(channel)

            for consumer in consumers:
                event = self._parse_consumer_payload(consumer, payload)

                if event is None:
                    continue

                logger.debug('got a consumer event', consumer_event=event)
                tg.create_task(consumer(event))

    async def _listen_to_notifications(self) -> None:
        channels = list(self._registry.keys())

        logger.debug('registering listeners for channels', channels=str(channels))

        for channel in channels:
            await self._connection.add_listener(channel, self._recieve_raw_notification)

    async def _recieve_raw_notification(self, _: asyncpg.Connection, __: int, channel: str, payload: str) -> None:
        """
        A callback triggered by asyncpg, moves raw notifications to a queue for further handling
        """
        logger.debug('got a raw notification', channel=channel, payload=payload)
        self._queue.put_nowait((channel, payload))

    def _parse_consumer_payload(self, consumer: Coroutine[Model], payload: str) -> Model | None:
        event = None
        type_annotations = inspect.get_annotations(consumer)

        for arg, cls in type_annotations.items():
            if arg == 'return':
                break

            try:
                event = cls.model_validate_json(payload)
            except ValidationError as e:
                logger.error(
                    'unable to obtain consumer event, skipping',
                    consumer=consumer.__name__,
                    payload=payload,
                    error=str(e),
                )
                continue

        return event

listener = Listener()
