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
            "Logged in as %s (%s) with %s guilds.",
            self.user.name,
            self.user.id,
            len(self.guilds),
        )

        guild = self.get_guild(config.Scraper.guild_id)
        if guild is None:
            return log.error("Guild %s not found.", config.Scraper.guild_id)

        log.info("Archiving guild %s (%s).", guild.name, guild.id)

        messages: list[tuple[int, str, str, int, int, int, str]] = []

        for channel in guild.text_channels:
            if not channel.permissions_for(guild.me).read_message_history:
                log.warning(
                    "Missing permissions to read message history in channel %s (%s).",
                    channel.name,
                    channel.id,
                )
                continue

            log.info("Archiving channel %s (%s).", channel.name, channel.id)

            try:
                    
                async for message in channel.history(limit=None):
                    if (
                        message.author.bot
                        or message.author.name == "Deleted User"
                        or message.content == ""
                        and not message.attachments
                    ):
                        continue

                    messages.append(
                        (
                            message.author.id,
                            message.content.replace("\x00", ""),
                            message.guild.name,
                            message.guild.id,
                            message.channel.id,
                            int(message.created_at.timestamp()),
                            message.attachments[0].url if message.attachments else None,
                        )
                    )

                    log.info(
                        "Archived message %s from %s (%s) in %s (%s).",
                        message.id,
                        message.author.name,
                        message.author.id,
                        message.channel.name,
                        message.channel.id,
                    )
            except Exception as e:
                log.error(
                    "Failed to archive channel %s (%s): %s, however we got %s messages.",
                    channel.name,
                    channel.id,
                    e,
                    len(messages),
                )

        log.info(
            "Archived %s messages in guild %s (%s).",
            len(messages),
            guild.name,
            guild.id,
        )

        await self.db.executemany(
            "INSERT INTO messages (user_id, message, guild_name, guild_id, channel_id, timestamp, attachment) VALUES ($1, $2, $3, $4, $5, $6, $7) ON CONFLICT (user_id, message, timestamp) DO NOTHING",
            messages,
        )

        log.info("Inserted %s messages into the database.", len(messages))

    async def close(self: "Archiver") -> None:
        await self.db.close()
        await super().close()
