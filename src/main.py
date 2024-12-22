import asyncio
from asyncio import Queue
from contextlib import asynccontextmanager

from dotenv import load_dotenv
import asyncpg
import structlog

import dataclasses
import os
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from sse_starlette import EventSourceResponse
from sse_starlette.event import ServerSentEvent
from tortoise.contrib.fastapi import RegisterTortoise

from src import models
# discovering is broken for now, will fix it later
from src.event_handlers import handle_user_created
from src.listener import listener

load_dotenv()
logger = structlog.get_logger(__name__)


@dataclasses.dataclass(frozen=True)
class DatabaseCredentials:
    host: str = os.environ.get('DATABASE_HOST')
    port: int = os.environ.get('DATABASE_PORT', 5432)
    username: str = os.environ.get('DATABASE_USER')
    password: str = os.environ.get('DATABASE_PASSWORD')
    database: str = os.environ.get('DATABASE_NAME')

    def get_dsn(self) -> str:
        return f'postgres://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'


creds = DatabaseCredentials()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    async with RegisterTortoise(_app, db_url=creds.get_dsn(), modules={"models": [models]}):
        connection = await asyncpg.connect(creds.get_dsn())
        listener.set_connection(connection)

        try:
            asyncio.create_task(listener.start())
        except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
            logger.info('closing the database connection')
            await connection.close()
        finally:
            logger.info('stopping the app')
        yield

app = FastAPI(debug=True, lifespan=lifespan)


@app.get("/sse")  # simplest stream generator
async def sse():
    async def gen():
        for i in range(99):
            yield i
            await asyncio.sleep(1)

    return EventSourceResponse(gen())


class Stream:
    def __init__(self) -> None:
        self._queue = Queue[ServerSentEvent]()

    def __aiter__(self) -> "Stream":
        return self

    async def __anext__(self) -> ServerSentEvent:
        return await self._queue.get()

    async def asend(self, value: ServerSentEvent) -> None:
        await self._queue.put(value)


_stream = Stream()
app.dependency_overrides[Stream] = lambda: _stream


@app.get("/listen")
async def sse_listener(stream: Stream = Depends()) -> EventSourceResponse:
    return EventSourceResponse(stream)


@app.post("/message", status_code=201)
async def send_message(message: str, stream: Stream = Depends()) -> None:
    await stream.asend(
        ServerSentEvent(data=message)
    )
