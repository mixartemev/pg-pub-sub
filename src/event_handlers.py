import asyncio
import enum
import structlog
from base_model import Model

from listener import listener

logger = structlog.get_logger(__name__)


class SubscriberChannel(enum.StrEnum):
    USERS = 'users'


class UserCreated(Model):
    email: str
    first_name: str
    last_name: str


@listener.subscribe(SubscriberChannel.USERS)
async def handle_user_created(user: UserCreated) -> None:
    logger.info('handling user creation', user=str(user))

    if user.first_name == 'Slow':
        # for concurrency check, other users won't be blocked
        logger.info('handling a long running user', user=str(user))
        await asyncio.sleep(30)

    logger.info('user creation has been handled', user=str(user))
    await asyncio.sleep(0)
