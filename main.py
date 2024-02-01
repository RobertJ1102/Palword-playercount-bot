import discord
import subprocess
from discord.ext import tasks
import datetime

# Discord Bot Token and Channel ID
TOKEN = 'MTIwMjYwMTU5MTg0NTI5MDAwNA.GR7SN5.aHLYGj8tDB4jD8uFVahRGOxslZIsQsx4GgJnn8'
STATUS_CHANNEL_ID = 1202585306419830864
LOG_CHANNEL_ID = 1202673591322284052
 
# RCON Server Configurations
SERVERS = [
    {"address": "localhost:25575", "password": "ojii0hoajkos"},
    {"address": "localhost:25585", "password": "ojii0hoajkos"},
    {"address": "localhost:25595", "password": "ojii0hoajkos"},
]

# Path to rcon.exe
RCON_EXE_PATH = "C:\\Discord Bots\\Palword-playercount-bot\\rcon\\rcon.exe"

# Store message IDs to edit later
message_ids = {}
current_players = {server['address']: set() for server in SERVERS}

# Discord Client Setup with Intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

def parse_player_info(player_list):
    players_info = {}
    lines = player_list.split('\n')[1:]  # Skip the header line
    for line in lines:
        if line:
            name, uuid, steamid = line.split(',')
            players_info[name] = {'uuid': uuid, 'steamid': steamid}
    return players_info

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    update_status.start()
    track_joins_and_leaves.start()

def fetch_rcon_data(server, command):
    try:
        # Constructing the command
        rcon_command = [RCON_EXE_PATH, "-a", server['address'], "-p", server['password'], command]
        
        # Running the command
        result = subprocess.run(rcon_command, capture_output=True, text=True)
        
        # Return output if successful, otherwise return error message
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"

@tasks.loop(minutes=1)
async def update_status():
    total_players = 0
    channel = client.get_channel(STATUS_CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {STATUS_CHANNEL_ID} not found.")
        return

    for server in SERVERS:
        server_info = fetch_rcon_data(server, "info")
        
        # Trim the server info to extract the version and server name
        version = server_info[server_info.find("[v"):server_info.find("]") + 1]
        server_name = server_info.replace('Welcome to Pal Server', '').strip()
        
        player_list = fetch_rcon_data(server, "showplayers")
        players = [player.split(',')[0] for player in player_list.split('\n')[1:] if player]  # Extracting player names
        total_players += len(players)

        embed = discord.Embed(title=server_name, description="**Players:**\n" + '\n'.join(players) if players else "No players currently online.")
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text=f"{version} • Last updated")

        if server['address'] in message_ids:
            try:
                msg = await channel.fetch_message(message_ids[server['address']])
                await msg.edit(embed=embed)
            except discord.NotFound:
                message_ids[server['address']] = (await channel.send(embed=embed)).id
        else:
            message_ids[server['address']] = (await channel.send(embed=embed)).id

    # Update Discord Bot Status with Total Players
    game = discord.Game(f"{total_players} Online Players")
    await client.change_presence(status=discord.Status.online, activity=game)

@tasks.loop(seconds=10)
async def track_joins_and_leaves():
    log_channel = client.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        print(f"Log channel with ID {LOG_CHANNEL_ID} not found.")
        return

    for server in SERVERS:
        # Fetch only the player list for join/leave tracking
        player_list = fetch_rcon_data(server, "showplayers")
        players = [player.split(',')[0] for player in player_list.split('\n')[1:] if player]  # Extracting player names
        new_player_set = set(players)
        old_player_set = current_players[server['address']]

        # Determine players who joined since the last update
        joined_players = new_player_set - old_player_set
        # Determine players who left since the last update
        left_players = old_player_set - new_player_set

        # Log join messages
        for player in joined_players:
            await log_channel.send(f"🟢 {player} has joined {server['address']}.")

        # Log leave messages
        for player in left_players:
            await log_channel.send(f"🔴 {player} has left {server['address']}.")

        # Update the stored player list to the new list
        current_players[server['address']] = new_player_set

client.run(TOKEN)
