import discord
import logging
import lavalink
import listen

from .utils.dataIO import dataIO
from discord.ext import commands 
from .utils import checks

log = logging.getLogger('Moe')

class listenmoe:
    def __init__(self, bot):
        self.bot = bot 
        
        # Start values
        self.now = None
        self.nowkpop = None
        self._linked_file = "config/linked_channels.json" 
        self._linked = dataIO.load_json(self._linked_file) 

        # Lavalink 
        if not hasattr(bot, 'lavalink'):
            lavalink.Client(bot=bot, password='youshallnotpass', loop=self.bot.loop, log_level=logging.INFO)
            self.bot.lavalink.register_hook(self.track_hook)           
                   
    async def hand(self, msg):
        before = self.now
        
        if msg.type == listen.message.SONG_INFO:             
            self.now = msg          
        else:
            if self.now:
                self.now = msg.raw   
                
        if before != self.now:  # avoid the first useless updates when starting the bot / loading the cog                
            await self.update_all_listen_moe_players()       
           
    async def handkpop(self, msg):
        before = self.nowkpop
            
        if msg.type == listen.message.SONG_INFO:             
            self.nowkpop = msg         
        else:
            if self.now:
                self.nowkpop = msg.raw   

        if before != self.nowkpop:  # avoid the first useless updates when starting the bot / loading the cog
            await self.update_all_listen_moe_players(kpop=True) 
           
    async def start(self):
        kp = listen.client.Client(kpop=True)
        kp.register_handler(self.handkpop)
        kp.loop.create_task(kp.start())
        
        cl = listen.client.Client()
        cl.register_handler(self.hand)
        cl.loop.create_task(cl.start())        

    async def track_hook(self, event):
        """Lavalink track hook called for each important event"""
        if isinstance(event, lavalink.Events.TrackStartEvent):  
        
            # Send now playing message
            c = self.bot.get_channel(event.player.channel)
            
            if c:              
                if 'kpop' in event.track.uri.lower():
                    color=int("3CA4E9", 16)
                    title = self.get_current_listen_moe(kpop=True)
                    thumb = "https://i.imgur.com/1RfgY17.png" 
                    event.track.uri = "http://listen.moe/kpop"
                else:
                    color=int("FF015B", 16)
                    title = self.get_current_listen_moe()                
                    thumb = "https://i.imgur.com/WtphvIv.png" 
                    event.track.uri = "http://listen.moe"
                                                 
                embed = discord.Embed(colour=color, title=title)
                               
                embed.set_image(url=thumb)
                    
                requester = self.bot.get_member(event.track.requester)                      

                if requester:
                    embed.set_author(name=requester.name, icon_url=requester.avatar_url or requester.default_avatar_url, url=event.track.uri)

                await self.send_new_np_msg(event.player, c, new_embed=embed)                                        
                    
        elif isinstance(event, lavalink.Events.QueueEndEvent):
            await self.delete_old_npmsg(event.player)    
            
    @commands.command(aliases=['p', 'moe', 'radio', 'start', 'listenmoe', 'jpop'])
    async def play(self, ctx, *, query=None):
        """
            {prefix}play (kpop)
        
        Starts the radio. You can specify kpop to start kpop radio instead.
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)
        and_skip = False
        if player.is_playing:
            if not ctx.channel.permissions_for(ctx.author).manage_guild:
                raise commands.errors.CheckFailure 
            else:
                and_skip = True
            
        if not player.is_connected:
            if not ctx.author.voice or not ctx.author.voice.channel:
                return await ctx.send('Sorry, you have to join a voice channel!')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect:
                return await ctx.send('Sorry, I lack the `connect` permission in this voice channel.')
            if not permissions.speak:
                return await ctx.send('Sorry, I lack the `speak` permission in this voice channel.')

            player.channel = ctx.channel.id
            player.npmsg = None
            await player.connect(ctx.author.voice.channel.id)
        else:
            if not ctx.author.voice or not ctx.author.voice.channel or player.connected_channel.id != ctx.author.voice.channel.id:
                return await ctx.send(f'I am already connected to `{player.connected_channel}`, what about joining my voice channel ?')

        if query and query[0].lower() == 'k':
            query = "https://listen.moe/kpop/fallback" # Assuming K-POP
        else:
            query = "https://listen.moe/fallback" 
            
        results = await self.bot.lavalink.get_tracks(query)            
            
        if not results or not results['tracks']:
            return await ctx.send("Sorry, I didn't found anything!")            

        track = results['tracks'][0]    
            
        player.add(requester=ctx.author.id, track=track)
        
        if and_skip:
            await player.skip()
        if not player.is_playing:
            await player.play()            
            
    @commands.command(aliases=['kp', 'k-pop', 'startkpop', 'radiokpop'])
    async def kpop(self, ctx):
        """
            {prefix}kpop
        
        Shortcurt to start the kpop radio.
        """    
        await ctx.invoke(self.play, query="k")          
    
    @checks.has_permissions(manage_guild=True)      
    @commands.command(aliases=['skip', 's'])
    async def stop(self, ctx):
        """
            {prefix}stop
        
        Disconnects the player from the voice channel.
        """    
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.connected_channel:
            return await ctx.send('I am not connected.')

        await self.disconnect_player(player)
        await ctx.send('Disconnecting....')            

    @checks.has_permissions(manage_guild=True)          
    @commands.command(aliases=['vol', 'v'])
    async def volume(self, ctx, volume: int=None):
        """
            {prefix}volume
        
        Adjusts the current volume.
        """      
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not volume:
            return await ctx.send(f'{player.volume}%')

        await player.set_volume(volume)
        await ctx.send(f'Volume set to {player.volume}%')    

    @commands.command(name='np', aliases=['currentsong', 'nowplaying', 'nplaying', 'current', 'now'])
    async def current_song(self, ctx):
        """
            {prefix}np
            
        Displays the current song informations.
        """
        player = self.bot.lavalink.players.get(ctx.guild.id)         
        current = player.current # stock it into a var avoid changes between the beg and the end of the command
        
        if not current:
            return await ctx.send("I'm not playing anything!", delete_after=20))
     
        if 'kpop' in current.uri.lower():
            color=int("3CA4E9", 16)
            title = self.get_current_listen_moe(kpop=True)
            thumb = "https://i.imgur.com/1RfgY17.png" 
            current.uri = "http://listen.moe/kpop"
        else:
            color=int("FF015B", 16)
            title = self.get_current_listen_moe()                
            thumb = "https://i.imgur.com/WtphvIv.png" 
            current.uri = "http://listen.moe"
            
        pos = lavalink.Utils.format_time(player.position).lstrip('0').lstrip(':')   
        dur = 'LIVE'
            
        requester = self.bot.get_member(current.requester)
        
        embed = discord.Embed(colour=color, title=title, description=f"`[{pos}/{dur}]`")
        embed.set_author(name=requester.name, icon_url=requester.avatar_url or requester.default_avatar_url, url=current.uri)
        embed.set_image(url=thumb)
        player.channel = ctx.channel.id
        await self.send_new_np_msg(player, ctx.channel, new_embed=embed)    

    @commands.group(aliases=["link", "linkedchannel", "lc"], invoke_without_command=True)
    async def linked(self, ctx, *, leftover_args):
        """
            {prefix}linked set [channel]
            {prefix}linked never            
            {prefix}linked reset
            {prefix}linked now
    
        Manages the linked channel on this server.
        """                       
        if ctx.invoked_subcommand is None: 
            return await ctx.invoke(self.linked_set, new_channel=leftover_args)    

    @linked.command(name="now", aliases=["queue", "display", "list", "liste", "info", "songlist"])
    async def linked_list(self, ctx):
        """   
            {prefix}linked now
    
        Displays the current linked channel on this server.
        """ 
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            return
        
        sid = str(ctx.guild.id)  
                        
        if sid in self._linked:    
            channel = discord.utils.find(lambda m: m.id == self._linked[sid], ctx.guild.channels)
            if not channel:
                self._linked.pop(sid, None)
                dataIO.save_json(self._linked_file, self._linked)    
                return await ctx.invoke(self.linked_list)
            await ctx.send("I'm currently linked to the {} voice channel.".format(f"`{channel}`"))               
        else:
            await ctx.send("I'm not linked to any voice channel on this server.")

    @checks.has_permissions(manage_guild=True)               
    @linked.command(name="set", aliases=["add", "are", "config"])
    async def linked_set(self, ctx,  *, new_channel):
        """   
            {prefix}linked set [channel]
            {prefix}linked set never    
    
        Sets the current linked channel on this server.
        """               
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            return
        
        sid = str(ctx.guild.id)  
            
        try:    
            channel = [c for c in ctx.guild.channels if (str(c.id) == new_channel or isinstance(new_channel, str) and c.name.lower() == new_channel.lower()) and isinstance(c, discord.VoiceChannel)][0]
            new_channel = channel.id
        except IndexError:
            return await ctx.send(f"Sorry, I didn't found any voice channel called `{new_channel}`")            

        self._linked[sid] = new_channel
        dataIO.save_json(self._linked_file, self._linked)
        await ctx.send("Understood, I'm now linked to the {} voice channel.".format(f"`{channel}`"))             
       
    @checks.has_permissions(manage_guild=True)          
    @linked.command(name="reset", aliases=["remove", "delete", "enable", "stop", "end", "off", "clean", "clear"])
    async def linked_delete(self, ctx):
        """   
            {prefix}linked reset
    
        Resets the current linked channel on this server.
        """ 
        if not ctx.channel.permissions_for(ctx.author).manage_guild:
            raise commands.errors.CheckFailure 
            
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            return
        else:
            sid = str(ctx.guild.id)          
        self._linked.pop(sid, None)
        dataIO.save_json(self._linked_file, self._linked)
        await ctx.send("There are no linked voice channels anymore!")  

    async def __local_check(self, ctx):
        """A check which applies to all commands in Music"""
        if not isinstance(ctx.channel, discord.abc.PrivateChannel):
            return True            
        if not ctx.guild:
            await ctx.send('```py\n{}\n```'.format("Sorry, my music commands are disabled in DMs."))
            return False
        return True         
            
    def get_current_listen_moe(self, kpop=False):
        """Returns the current song title on LISTEN.moe"""     
        now = self.bot.cogs['listenmoe'].now
        if kpop:
            now = self.bot.cogs['listenmoe'].nowkpop               
        if now:
            if not isinstance(now, dict):
                if now.artists:
                    return f"{now.artists[0].name_romaji or now.artists[0].name} - {now.title}" 
                else:
                    return f"{now.title}"   
            else: # if now = msg.raw 
                try:
                    if 'nameRomaji' in artists:
                        artist = now['d']['song']['artists'][0]['nameRomaji']
                    elif 'name' in artists:
                        artist = now['d']['song']['artists'][0]['name']
                except KeyError:
                    artist = False
                title = now['d']['song']['title']
                if artist:
                    return f"{artist} - {title}"
                else:
                    return  f"{title}"         

        return f"LISTEN.moe {'K-POP' if kpop else 'J-POP'}"              

    async def disconnect_player(self, player):
        """Disconnects a player and clean some stuffs"""  
        guild = self.bot.get_guild(int(player.guild_id))
        if guild: # maybe it's from on_guild_remove
            gid = guild.id           
        else:
            gid = int(player.guild_id)
        
        # Cleaning some stuffs
        await self.delete_old_npmsg(player)            
        player.queue.clear()        
        await player.disconnect()
        self.bot.lavalink.players.remove(gid) 
        
        guild_info = f"{guild.id}/{guild.name}" if guild else f"{gid}"
        log.info(f"[Disconnecting] {guild_info}")              
                    
    async def delete_old_npmsg(self, player): 
        """Deletes the old np messages or not without raison a discord exception"""
        if player.npmsg:
            try:
                await player.npmsg.delete()
            except discord.HTTPException:
                pass    

    async def send_new_np_msg(self, player, channel, new_embed): 
        """Sends a new np msg and maybe delete the old one / or edit it"""  
        # Check if it is worth to edit instead
        try_edit = False
        if player.npmsg:
            async for entry in channel.history(limit=5):
                if entry: # idk 
                    if entry.id == player.npmsg.id:
                        try_edit = True
                        break 
        
        # Send or edit the old message
        if try_edit:            
            try:
                await player.npmsg.edit(embed=new_embed, content=None)
            except discord.HTTPException: 
                await self.delete_old_npmsg(player)
                player.npmsg = await channel.send(embed=embed)
        else:                
            await self.delete_old_npmsg(player)
            player.npmsg = await channel.send(embed=new_embed) 

    def listen_moe_update(self, current):
        """Updates listen moe song title in current players"""     
        if "listen.moe" in current.uri.lower():
            if 'listenmoe' in self.bot.cogs:
                if 'kpop' in current.uri.lower():
                    current.title = self.get_current_listen_moe(kpop=True)             
                else:
                    current.title = self.get_current_listen_moe()               
            
    async def update_all_listen_moe_players(self, kpop=False):
        """Updates all listen moe players to display the new current song"""          
        playing = self.bot.lavalink.players.find_all(lambda p: p.is_playing and p.current) # maybe useless to check p.current but who knows ?
        for p in playing:
            if 'kpop' in p.current.uri.lower() and not kpop: # basic checks to ignore useless updates
                continue
            elif 'kpop' not in p.current.uri.lower() and kpop:
                continue      
                
            self.listen_moe_update(p.current)     
            c = self.bot.get_channel(p.channel)
            
            if c:              
                if 'kpop' in p.current.uri.lower():
                    color=int("3CA4E9", 16)
                    thumb = "https://i.imgur.com/1RfgY17.png" 
                else:
                    color=int("FF015B", 16)              
                    thumb = "https://i.imgur.com/WtphvIv.png" 
                
                embed = discord.Embed(colour=color, title=p.current.title)
                               
                embed.set_image(url=thumb)
                    
                requester = self.bot.get_member(p.current.requester)                      

                if requester:
                    embed.set_author(name=requester.name, icon_url=requester.avatar_url or requester.default_avatar_url, url=p.current.uri)

                await self.send_new_np_msg(p, c, new_embed=embed)        

    async def connect_linked(self):
        """Allows to auto-connect the bot to every linked player."""  
        for guild in self.bot.guilds:
            if str(guild.id) in self._linked:
                c = guild.get_channel(self._linked[str(guild.id)])
                if c:
                    me = c.guild.get_member(self.bot.user.id)
                    if not c.permissions_for(me).connect:   
                        continue
                    if not c.permissions_for(me).speak: 
                        continue                 
                    player = self.bot.lavalink.players.get(guild.id)
                    player.channel = None
                    player.npmsg = None
                    await player.connect(c.id)
                    results = await self.bot.lavalink.get_tracks("https://listen.moe/fallback")
                    track = results['tracks'][0]
                    player.add(requester=self.bot.user.id, track=track)
                    if not player.is_playing: # Maybe better to check even if it's not supposed to be playing
                        await player.play()      

    async def on_guild_update(self, before, after):
        if before.region != after.region:
            log.warning("[Guild] \"%s\" changed regions: %s -> %s" % (after.name, before.region, after.region))  
            if after.id in self.bot.lavalink.players:
                player = self.bot.lavalink.players.get(after.id)
                cid = int(player.channel_id)
                await player.connect(cid)
            
    async def on_guild_remove(self, guild):   
        if guild.id in self.bot.lavalink.players:
            player = self.bot.lavalink.players.get(guild.id)
            await self.disconnect_player(player)       

    async def on_ready(self):
        await self.start()  
        await self.connect_linked()
                    
def setup(bot):
    bot.add_cog(listenmoe(bot))
