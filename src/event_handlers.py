import enum
import structlog
from src.base_model import UserCreated
from sse_starlette.event import ServerSentEvent

from src.listener import listener
from src.stream import stream

logger = structlog.get_logger(__name__)


class SubscriberChannel(enum.StrEnum):
    USERS = 'users'
    ORDER_STTS = 'orders_upd_stts'


@listener.subscribe(SubscriberChannel.USERS)
async def handle_user_created(user: UserCreated) -> None:
    logger.info('user creation has been handled, sending to stream', user=str(user))

    await stream.asend(
        ServerSentEvent(data=user.json())
    )
