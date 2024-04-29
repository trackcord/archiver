from typing import TYPE_CHECKING

from discord import Client

import config
from tools.managers import database, logging

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class Archiver(Client):
    def __init__(self: "Archiver", *args, **kwargs) -> None:
        super().__init__(
            command_prefix="---",
            help_command=None,
            chunk_guilds_at_startup=False,
            *args,
            **kwargs,
        )
        self.db: database.Pool = None

    async def setup_hook(self: "Archiver") -> None:
        self.db = await database.connect()

    async def on_ready(self: "Archiver") -> None:
        log.info(
            f"Logged in as {self.user.name} ({self.user.id}) with {len(self.guilds)} guilds."
        )

        # get all config.Scraper.guild_id channels
        # get all messages from the channels
        # archive the messages

        guild = self.get_guild(config.Scraper.guild_id)
        if guild is None:
            return log.error("Guild %s not found.", config.Scraper.guild_id)

        log.info("Archiving guild %s (%s).", guild.name, guild.id)

        messages: list[dict[str, str]] = []

        for channel in guild.text_channels:
            if not channel.permissions_for(guild.me).read_message_history:
                log.warning(
                    "Missing permissions to read message history in channel %s (%s).",
                    channel.name,
                    channel.id,
                )
                continue

            log.info("Archiving channel %s (%s).", channel.name, channel.id)

            async for message in channel.history(limit=None):
                if (
                    message.author.bot
                    or message.content == ""
                    and not message.attachments
                ):
                    continue

                messages.append(
                    {
                        "user_id": message.author.id,
                        "message": message.content,
                        "guild_name": message.guild.name,
                        "guild_id": message.guild.id,
                        "timestamp": int(message.created_at.timestamp()),
                        "attachment": (
                            message.attachments[0].url if message.attachments else None
                        ),
                    }
                )

                log.info(
                    "Archived message %s (%s) from %s in %s (%s).",
                    message.id,
                    message.author.name,
                    message.author.id,
                    channel.name,
                    channel.id,
                )

        log.info("Archived %s messages.", len(messages))

        await self.db.execute_many(
            "INSERT INTO messages (user_id, message, guild_name, guild_id, timestamp, attachment) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (user_id, message, timestamp) DO NOTHING",
            messages,
        )

        log.info("Inserted %s messages.", len(messages))

    async def close(self: "Archiver") -> None:
        await self.db.close()
        await super().close()
