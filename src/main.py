from dotenv import load_dotenv
import asyncio
import asyncpg
import structlog

import dataclasses
import os

from listener import listener
# discovering is broken for now, will fix it later
from event_handlers import handle_user_created

load_dotenv()
logger = structlog.get_logger(__name__)


@dataclasses.dataclass(frozen=True)
class DatabaseCredentials:
    host: str = os.environ.get('DATABASE_HOST')
    port: int = os.environ.get('DATABASE_PORT', 5432)
    username: str = os.environ.get('DATABASE_USERNAME')
    password: str = os.environ.get('DATABASE_PASSWORD')
    database: str = os.environ.get('DATABASE_NAME')

    def get_dsn(self) -> str:
        return f'postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'


async def main() -> None:
    creds = DatabaseCredentials()
    logger.info('openning a database connection')

    # TODO use a connection pool here
    connection = await asyncpg.connect(dsn=creds.get_dsn())
    listener.set_connection(connection)

    try:
        await listener.start()
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        logger.info('closing the database connection')
        await connection.close()
    finally:
        logger.info('stopping the app')


if __name__ == '__main__':
    # TODO try uvloop
    asyncio.run(main())
