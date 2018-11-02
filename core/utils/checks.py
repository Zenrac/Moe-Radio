"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz
Copyright (c) 2018 Zenrac

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


from discord.ext import commands

#  The permission system of the bot is based on a "just works" basis
#  You have permissions and the bot has permissions. If you meet the permissions
#  required to execute the command (and the bot does as well) then it goes through
#  and you can execute the command.
#  Certain permissions signify if the person is a moderator (Manage Server) or an
#  admin (Administrator). Having these signify certain bypasses.
#  Of course, the owner will always be able to execute commands.


async def check_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    resolved = ctx.channel.permissions_for(ctx.author)
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, check=check)
    return commands.check(pred)


async def check_guild_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_guild_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_guild_permissions(ctx, perms, check=check)
    return commands.check(pred)

#  These do not take channel overrides into account


def is_mod():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {'manage_guild': True})
    return commands.check(pred)


def is_admin():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {'administrator': True})
    return commands.check(pred)


def mod_or_permissions(**perms):
    perms['manage_guild'] = True

    async def predicate(ctx):
        return await check_guild_permissions(ctx, perms, check=any)
    return commands.check(predicate)


def dj_or_permissions(**perms):

    async def predicate(ctx):
        if ctx.guild:
            if [r for r in ctx.author.roles if r.name.lower() == "dj"]:
                return True
            if is_alone(ctx.author):
                return True
        return await check_guild_permissions(ctx, perms, check=any)
    return commands.check(predicate)


def dm_or_permissions(**perms):
    async def predicate(ctx):
        if ctx.guild is None:
            return True
        return await check_guild_permissions(ctx, perms, check=any)
    return commands.check(predicate)


def admin_or_permissions(**perms):
    perms['administrator'] = True

    async def predicate(ctx):
        return await check_guild_permissions(ctx, perms, check=any)
    return commands.check(predicate)


def is_in_guilds(*guild_ids):
    def predicate(ctx):
        guild = ctx.guild
        if guild is None:
            return False
        return guild.id in guild_ids
    return commands.check(predicate)


def is_alone(author):
    if not author.guild.me.voice or not author.voice:
        return False
    num_voice = sum(1 for m in author.voice.channel.members if not (m.voice.deaf or m.bot or m.voice.self_deaf))
    if num_voice == 1 and author.guild.me.voice.channel == author.voice.channel:
        return True
    return False


def is_lounge_cpp():
    return is_in_guilds(145079846832308224)
