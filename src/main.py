import asyncio
from contextlib import asynccontextmanager
from typing_extensions import AsyncIterable

from dotenv import load_dotenv
import asyncpg
import structlog

import dataclasses
import os
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from sse_starlette import EventSourceResponse
from tortoise.contrib.fastapi import RegisterTortoise

from src.base_model import UserPyd
from src.stream import Stream, app_stream

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
            yield
        except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
            logger.info('closing the database connection')
            await connection.close()
        finally:
            logger.info('stopping the app')

app = FastAPI(debug=True, lifespan=lifespan)


@app.get("/new/{uid}", response_model=UserPyd)
async def sse_listener(uid: int, user_stream: AsyncIterable = Depends(app_stream)) -> EventSourceResponse:
    logger.info('reading events for the user create', user_id=uid, user_stream=user_stream)

    return EventSourceResponse(user_stream)


@app.get("/upd/{uid}", response_model=UserPyd)
async def sse_listener(uid: int, user_stream: AsyncIterable = Depends(app_stream)) -> EventSourceResponse:
    logger.info('reading events for the user update', user_id=uid, user_stream=user_stream)

    return EventSourceResponse(user_stream)
