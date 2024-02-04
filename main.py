import discord
import subprocess
from discord.ext import tasks
import datetime
import asyncio
import json

# Discord Bot Token and Channel ID
TOKEN = 'MTIwMjYwMTU5MTg0NTI5MDAwNA.G3mugb.i0QA2vSSJtQg3QdGjva9-koNiVKaaC6OrCJIUg'
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
#message_ids = {}
current_players = {server['address']: {} for server in SERVERS}

# Discord Client Setup with Intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

message_ids_file = 'message_ids.json'

def save_message_id(server_address, message_id):
    try:
        # Try opening the file in read/write mode, creating it if it doesn't exist
        with open(message_ids_file, 'r+') as file:
            try:
                message_ids = json.load(file)
            except json.JSONDecodeError:
                message_ids = {}  # File is empty, proceed with an empty dict
    except FileNotFoundError:
        message_ids = {}  # File does not exist, proceed with an empty dict

    # Update the message ID for the server
    message_ids[server_address] = message_id

    # Move back to the beginning of the file before writing
    with open(message_ids_file, 'w') as file:
        json.dump(message_ids, file)



def load_message_ids():
    try:
        with open(message_ids_file, 'r') as file:
            content = file.read().strip()
            if content:
                message_ids = json.loads(content)
                print("Loaded message IDs:", message_ids)  # Debug print
                return message_ids
            else:
                return {}
    except FileNotFoundError:
        return {}

message_ids = load_message_ids()

def parse_player_info(player_list):
    players_info = {}
    lines = player_list.split('\n')[1:]
    for line in lines:
        if line:
            name, uuid, steamid = line.split(',')
            players_info[name] = {'uuid': uuid, 'steamid': steamid}
    return players_info


async def update_or_send_message(channel, server_address, embed):
    message_id = message_ids.get(server_address)
    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)
            print(f"Edited message {message_id} for {server_address}")  # Debug print
        except discord.NotFound:
            msg = await channel.send(embed=embed)
            save_message_id(server_address, msg.id)
            print(f"Sent new message and saved ID {msg.id} for {server_address}")  # Debug print
    else:
        msg = await channel.send(embed=embed)
        save_message_id(server_address, msg.id)
        print(f"Sent new message and saved ID {msg.id} for {server_address}")  # Debug print

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    update_status.start()
    track_joins_and_leaves.start()
    auto_restart_sequence.start()

async def fetch_rcon_data(server, command, retries=3, timeout=20):
    attempt = 0
    while attempt < retries:
        try:
            rcon_command = [RCON_EXE_PATH, "-a", server['address'], "-p", server['password'], command]
            process = await asyncio.create_subprocess_exec(
                *rcon_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
                if process.returncode == 0:
                    return stdout.decode().strip()
                else:
                    print(f"Error executing RCON command: {stderr.decode().strip()}")
            except asyncio.TimeoutError:
                print(f"Timeout executing RCON command on attempt {attempt + 1}")
                # Optionally kill the process if it's still running
                if process.returncode is None:
                    process.kill()
                    await process.communicate()

        except Exception as e:
            print(f"Exception executing RCON command: {str(e)}")
        attempt += 1
    return "Error: RCON command failed after retries"

async def update_or_send_message(channel, server_address, embed):
    if server_address in message_ids:
        try:
            msg = await channel.fetch_message(message_ids[server_address])
            await msg.edit(embed=embed)
        except discord.NotFound:
            # If the message was not found, send a new one
            msg = await channel.send(embed=embed)
            save_message_id(server_address, msg.id)
    else:
        # No message ID stored, send a new message
        msg = await channel.send(embed=embed)
        save_message_id(server_address, msg.id)

def format(address):
    # replace with server name
    if address == "localhost:25575":
        return "EU1"
    elif address == "localhost:25585":
        return "EU2"
    elif address == "localhost:25595":
        return "EU3"

@tasks.loop(hours=5, minutes=50)
async def auto_restart_sequence():
    print("Starting 6h count down sequence")
    for server in SERVERS:
        print(f"Initiating shutdown sequence for {server['address']}.")
        await fetch_rcon_data(server, "shutdown 600")  # Shutdown in 10 minutes
        await asyncio.sleep(300)  # Wait 5 minutes
        await fetch_rcon_data(server, "broadcast Server_restarting_in_5_minutes.")
        await asyncio.sleep(240)  # Wait 4 minutes
        await fetch_rcon_data(server, "broadcast Server_restarting_in_1_minute.")
        await asyncio.sleep(50)  # Final minute
        await fetch_rcon_data(server, "save")

@tasks.loop(minutes=1)
async def update_status():
    total_players = 0
    status_channel = client.get_channel(STATUS_CHANNEL_ID)
    if status_channel is None:
        print(f"Channel with ID {STATUS_CHANNEL_ID} not found.")
        return

    for server in SERVERS:
        server_info = await fetch_rcon_data(server, "info")
        version = server_info[server_info.find("[v"):server_info.find("]") + 1]
        server_name = server_info.replace('Welcome to Pal Server', '').strip()
        player_list = await fetch_rcon_data(server, "showplayers")
        players = [player.split(',')[0] for player in player_list.split('\n')[1:] if player]
        total_players += len(players)
        embed = discord.Embed(title=server_name, description="**Players:**\n" + '\n'.join(players) if players else "No players currently online.")
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=f"{version} • Last updated")
        await update_or_send_message(status_channel, server['address'], embed)

    game = discord.Game(f"{total_players} Online Players")
    await client.change_presence(status=discord.Status.online, activity=game)


@tasks.loop(seconds=10)
async def track_joins_and_leaves():
    log_channel = client.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        print(f"Log channel with ID {LOG_CHANNEL_ID} not found.")
        return

    for server in SERVERS:
        player_list = await fetch_rcon_data(server, "showplayers")
        # Parse the player list into a dict mapping names to a dict of the uuid and steamid
        new_player_info = {player.split(',')[0]: {'uuid': player.split(',')[1], 'steamid': player.split(',')[2]}
                           for player in player_list.split('\n')[1:] if player}
        new_player_names = set(new_player_info.keys())
        old_player_info = current_players[server['address']]
        old_player_names = set(old_player_info.keys())

        # Determine players who joined since the last update
        joined_players = new_player_names - old_player_names
        # Determine players who left since the last update
        left_players = old_player_names - new_player_names

        # Log join messages with name, steamid, and uuid
        for player in joined_players:
            await log_channel.send(f"🟢 {player} has joined {format(server['address'])}. "
                                   f"SteamID: {new_player_info[player]['steamid']}, "
                                   f"UUID: {new_player_info[player]['uuid']}")

        # Log leave messages with name, steamid, and uuid
        for player in left_players:
            await log_channel.send(f"🔴 {player} has left {format(server['address'])}. "
                                   f"SteamID: {old_player_info[player]['steamid']}, "
                                   f"UUID: {old_player_info[player]['uuid']}")

        # Update the stored player list to the new list
        current_players[server['address']] = new_player_info

client.run(TOKEN)
