import enum
import structlog
from src.base_model import UserPyd
from sse_starlette.event import ServerSentEvent

from src.listener import listener
from src.stream import app_stream

logger = structlog.get_logger(__name__)


class SubscriberChannel(enum.StrEnum):
    USER_NEW = 'user_new'
    USER_UPD = 'user_upd'


@listener.subscribe(SubscriberChannel.USER_NEW)
async def handle_user_created(user: UserPyd) -> None:
    logger.info('user creation has been handled, sending to stream', user=str(user))

    await app_stream.asend(
        user_id=user.id,
        value=ServerSentEvent(data=user.json()),
    )


@listener.subscribe(SubscriberChannel.USER_UPD)
async def handle_user_created(user: UserPyd) -> None:
    logger.info('user creation has been handled, sending to stream', user=str(user))

    await app_stream.asend(
        user_id=user.id,
        value=ServerSentEvent(data=user.json()),
    )
