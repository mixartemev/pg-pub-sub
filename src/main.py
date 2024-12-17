from contextlib import asynccontextmanager

from dotenv import load_dotenv
import asyncio
import asyncpg
import structlog

import dataclasses
import os
from typing import AsyncGenerator

from fastapi import FastAPI
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
            await listener.start()
        except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
            logger.info('closing the database connection')
            await connection.close()
        finally:
            logger.info('stopping the app')
        yield

app = FastAPI(debug=True, lifespan=lifespan)
