import discord
import subprocess
from discord.ext import tasks

# Discord Bot Token and Channel ID
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
CHANNEL_ID = 1202585306419830864  # Replace with your channel ID

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

# Discord Client Setup with Intents
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    update_status.start()

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
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {CHANNEL_ID} not found.")
        return

    for server in SERVERS:
        server_info = fetch_rcon_data(server, "info")
        player_list = fetch_rcon_data(server, "showplayers")
        players = [player.split(',')[0] for player in player_list.split('\n')[1:] if player]  # Extracting player names
        total_players += len(players)

        embed = discord.Embed(title=server_info, description="Players:\n" + '\n'.join(players))
        embed.set_footer(text="Last updated")

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

client.run(TOKEN)
