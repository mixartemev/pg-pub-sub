# PG pub-sub

A toy PoC of the [pub-sub pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber)
built with the PostgreSQL [NOTIFY/LISTEN](https://www.postgresql.org/docs/current/sql-notify.html) feature
for education and fun -> shit code quality and no tests

The approach itself may help to reduce coupling in your domain logic by
splitting handlers through different bounded contexts and prevent "spaghetti" code.

## Usage example

Define your domain events and handlers:

```python
# your domain event that occurs in its own bounded context
class UserCreated(Model):
    email: str
    first_name: str
    last_name: str


# a domain event handler in a separate bounded context that has to know about your event
@listener.subscribe(channel='users')
async def handle_user_created(user: UserCreated) -> None:
    logger.info('handling user creation', user=str(user))

    # some domain logic ...


# your service initialization
async def main() -> None:
    creds = DatabaseCredentials()
    # probably better use with connection pool
    connection = await asyncpg.connect(dsn=creds.get_dsn())
    listener.set_connection(connection)

    try:
        await listener.start()
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        logger.info('closing the database connection')
        await connection.close()
    finally:
        logger.info('stopping the app')

```

Produce events via PG from your business code or directly via SQL:

```sql
SELECT pg_notify('user_new', '{"id": 1, "name": "Foma"}');
```

```sql
SELECT pg_notify('user_upd', '{"id": 1, "name": "Vasya"}');
```

## Installation

Tested locally on bare metal Python3.12, no tests provided yet

```sh
python3 -m venv venv
pip install -r requirements.txt
make compose
```

Open db shell for event triggering
```sh
make db-shell
```
