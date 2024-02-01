import discord
import asyncio
from discord.ext import tasks
from aiorcon import RCON

# Discord Bot Token
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'

# RCON Server Configurations
SERVERS = [
    {"ip": "server_1_ip", "port": 25575, "password": "server_1_password"},
    {"ip": "server_2_ip", "port": 25576, "password": "server_2_password"},
    # Add more servers as needed
]

# Discord Client Setup
client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    update_status.start()

async def fetch_players(server):
    try:
        async with RCON.create(server['ip'], server['port'], server['password']) as rcon:
            response = await rcon("showplayers")
            players = response.split('\n')[1:]  # Skip header row
            return [player.split(',')[0] for player in players if player]
    except Exception as e:
        print(f"Error connecting to server {server['ip']}: {e}")
        return []

@tasks.loop(seconds=60)  # Update every 60 seconds
async def update_status():
    all_player_names = []
    tasks = [fetch_players(server) for server in SERVERS]
    results = await asyncio.gather(*tasks)

    for player_names in results:
        all_player_names.extend(player_names)

    total_players = len(all_player_names)

    # Update Discord Bot Status
    game = discord.Game(f"{total_players} players online across all servers")
    await client.change_presence(status=discord.Status.online, activity=game)

    # Update Embed in a specific channel
    channel = client.get_channel(YOUR_CHANNEL_ID)  # Replace with your channel ID
    embed = discord.Embed(title="Current Players Across All Servers", description="\n".join(all_player_names))
    await channel.send(embed=embed)

client.run(TOKEN)
