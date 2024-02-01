import discord
import subprocess
from discord.ext import tasks

# Discord Bot Token
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'

# RCON Server Configurations
SERVERS = [
    {"address": "localhost:25575", "password": "server_1_password"},
    {"address": "localhost:25576", "password": "server_2_password"},
    # Add more servers as needed
]

# Path to rcon.exe
RCON_EXE_PATH = "C:\\Discord Bots\\Palword-playercount-bot\\rcon\\rcon.exe"

# Discord Client Setup
client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    update_status.start()

def fetch_players(server):
    try:
        # Constructing the command
        command = [RCON_EXE_PATH, "-a", server['address'], "-p", server['password'], "showplayers"]
        
        # Running the command
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Return output if successful, otherwise return error message
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"

@tasks.loop(seconds=60)  # Update every 60 seconds
async def update_status():
    all_player_names = []
    
    for server in SERVERS:
        response = fetch_players(server)
        if response.startswith('Error') or response.startswith('Exception'):
            print(response)
        else:
            players = response.split('\n')
            all_player_names.extend(players)

    total_players = len(all_player_names)

    # Update Discord Bot Status
    game = discord.Game(f"{total_players} Online Players")
    await client.change_presence(status=discord.Status.online, activity=game)

    # Update Embed in a specific channel
    channel = client.get_channel("1202585306419830864")  # Replace with your channel ID
    embed = discord.Embed(title="Current Players Across All Servers", description="\n".join(all_player_names))
    await channel.send(embed=embed)

client.run(TOKEN)
