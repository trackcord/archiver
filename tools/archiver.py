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

        for channel in guild.text_channels:
            log.info("Archiving channel %s (%s).", channel.name, channel.id)

            async for message in channel.history(limit=None):
                if (
                    message.author.bot
                    or message.content == ""
                    and not message.attachments
                ):
                    continue

                log.info(
                    "Archived message %s (%s) by %s (%s).",
                    message.content,
                    message.id,
                    message.author.name,
                    message.author.id,
                )

                await self.db.execute(
                    "INSERT INTO messages (user_id, message, guild_name, guild_id, timestamp, attachment) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (user_id, message, timestamp) DO NOTHING",
                    message.author.id,
                    message.content,
                    message.guild.name,
                    message.guild.id,
                    int(message.created_at.timestamp()),
                    message.attachments[0].url if message.attachments else None,
                )

            log.info("Archived channel %s (%s).", channel.name, channel.id)

        log.info("Archived guild %s (%s).", guild.name, guild.id)

    async def disconnect(self: "Archiver") -> None:
        await self.db.close()
        await super().close()
