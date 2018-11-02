import sys
import discord
import asyncio
import logging
import traceback

from .utils.dataIO import dataIO
from discord.ext import commands

try:
    import uvloop
except ImportError:  # uvloop not available on Windows
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

log = logging.getLogger('Moe')


class Moe(commands.AutoShardedBot):

    def __init__(self):
        # Get settings from json
        self.settings = dataIO.load_json("config/settings.json")

        # Init the bot
        super().__init__(command_prefix=commands.when_mentioned_or(self.settings['PREFIX']), case_insensitive=True,
                         description='A very basic bot for LISTEN.moe radio.')

        self.init_ok = False

        # Load cog(s)
        extension = "listen"

        try:
            self.load_extension("core." + extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            log.info('Failed to load extension {}\n{}'.format(extension, exc))

    def get_member(self, id):
        try:
            return [m for m in self.get_all_members() if m.id == id][0]
        except IndexError:
            return None

    async def on_message(self, message):
        if not self.init_ok:
            return

        if not message.author.bot:
            await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        channel = ctx.channel
        can_send = channel.permissions_for(ctx.me).send_messages

        if isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            if can_send:
                log.info(f"{error}.. Sending help...")
                return await ctx.send(f"```cs\n{error}```\n\nMaybe try to use ``{ctx.prefix}help {ctx.command}``")
            else:
                log.info("Can't send help - Missing Permissions")
                return

        elif isinstance(error, commands.errors.CheckFailure):
            if can_send:
                return await ctx.channel.send("Sorry, you don't have enough permissions to use this command.", delete_after=10)
            else:
                log.info("Can't send permissions failure message - Missing Permissions")
                return

        elif isinstance(error, commands.CommandNotFound):
            return

        else:
            if isinstance(error, commands.CommandInvokeError):
                if isinstance(error.original, discord.errors.Forbidden):
                    log.info("discord.errors.Forbidden: FORBIDDEN (status code: 403): Missing Permissions")
                    return
                if isinstance(error.original, discord.errors.NotFound):
                    # log.info("discord.errors.NotFound: NotFound (status code: 404): Message not found")
                    return

            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)

            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

            log.error(f'Exception in command {ctx.command.name}: {error}')

    async def on_ready(self):
        users = len(set(self.get_all_members()))
        servers = len(self.guilds)
        channels = len([c for c in self.get_all_channels()])
        log.info("-----------------")
        log.info(str(self.user))
        log.info("{} server{}".format(servers, 's' if servers > 1 else ''))
        log.info("{} shard{}".format(self.shard_count, 's' if self.shard_count > 1 else ''))
        log.info("{} channel{}".format(channels, 's' if channels > 1 else ''))
        log.info("{} users".format(users))
        log.info("Prefix: {}".format(self.settings['PREFIX']))
        log.info("-----------------")
        self.init_ok = True

    async def on_shard_ready(self, shard_id):
        log.info(f"Shard {shard_id} is ready")

    def run(self):
        super().run(self.settings['TOKEN'], reconnect=True)
