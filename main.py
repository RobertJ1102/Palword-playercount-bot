import discord
from discord.ext import tasks
from valve.rcon import RCON

# Discord Bot Token
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'

# RCON Details
RCON_IP = 'localhost'  # Or the appropriate IP
RCON_PORT = 25575
RCON_PASSWORD = 'your_rcon_password'

# Discord Client Setup
client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    update_status.start()

@tasks.loop(seconds=60)  # Update every 60 seconds
async def update_status():
    total_players = 0
    player_names = []
    
    # Connect to RCON and execute command
    with RCON((RCON_IP, RCON_PORT), RCON_PASSWORD) as rcon:
        response = rcon.execute("showplayers").body
        players = response.split('\n')[1:]  # Skip header row
    
    for player in players:
        if player:
            name = player.split(',')[0]
            player_names.append(name)
            total_players += 1

    # Update Discord Bot Status
    game = discord.Game(f"{total_players} players online")
    await client.change_presence(status=discord.Status.online, activity=game)

    # Update Embed in a specific channel
    channel = client.get_channel(YOUR_CHANNEL_ID)
    embed = discord.Embed(title="Current Players", description="\n".join(player_names))
    await channel.send(embed=embed)

client.run(TOKEN)
