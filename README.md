# Moe-Radio

Moe-Radio is a very simple discord bot for LISTEN.moe (J-POP and K-POP) using discord.py (rewrite). It only have about 5 commands.<br><br>- You can link a voice channel to make the bot plays the radio forever.<br> - The now playing message is editing itself displaying which current song is playing.

## Requirements :<br>
- Python 3.6+<br>
- [discord.py (rewrite)](https://github.com/Rapptz/discord.py/tree/rewrite)
- [Lavalink.py](https://github.com/Devoxin/Lavalink.py)
- [Listen](https://github.com/Yarn/Listen)
<br><br>
## How to use :<br>
- You have to edit ```config/settings.json``` by adding your token, your ID and the prefix you want.
- Install Lavalink.py, Listen and discord.py (rewrite)
- Download Lavalink.jar (V3) and run it with Java 9+ (tested on Java 10)
- Start run.sh (linux) or run.bat (windows)
<br><br>
## Commands :<br>
- ```(prefix)play``` or ```(prefix)play kpop``` : starts a radio
- ```(prefix)kpop``` : same as ```(prefix)play kpop```
- ```(prefix)np``` : displays the current song
- ```(prefix)volume``` : adjusts the current player volume
- ```(prefix)stop``` : disconnects the bot
