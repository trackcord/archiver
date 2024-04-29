from json import dumps, loads
from typing import Any, Optional

from asyncpg import Connection, Pool
from asyncpg import Record as DefaultRecord
from asyncpg import create_pool
from munch import DefaultMunch, Munch

from config import Database
from tools.managers import logging

log = logging.getLogger(__name__)


class Record(DefaultRecord):
    def __getattr__(self: "Record", attr: str) -> Any:
        return self.get(attr)


def encode_jsonb(value: Any) -> str:
    return dumps(value)


def decode_jsonb(value: str) -> Munch:
    return DefaultMunch.fromDict(loads(value))


async def init(connection: Connection):
    await connection.set_type_codec(
        "jsonb",
        schema="pg_catalog",
        encoder=encode_jsonb,
        decoder=decode_jsonb,
    )


async def setup(pool: Pool) -> Pool:
    async with pool.acquire() as connection:
        connection.get_server_pid()
        version: str = ".".join(map(str, connection.get_server_version()))

    log.info(
        "Established a connection to PostgreSQL (%s) on %s.", version, Database.host
    )
    return pool


async def connect() -> Pool:
    pool: Optional[Pool] = await create_pool(
        f"postgres://{Database.username}:{Database.password}@{Database.host}/{Database.name}",
        init=init,
        record_class=Record,
        statement_cache_size=0,
    )
    if not pool:
        raise Exception("Could not establish a connection to the PostgreSQL server!")

    return await setup(pool)
