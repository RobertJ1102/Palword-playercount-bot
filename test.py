import asyncio
from aiorcon import RCON

# RCON Server Configurations
SERVERS = [
    {"ip": "server_1_ip", "port": 25575, "password": "server_1_password"},
    {"ip": "server_2_ip", "port": 25576, "password": "server_2_password"},
    # Add more servers as needed
]

async def test_rcon(server):
    try:
        async with RCON.create(server['ip'], server['port'], server['password']) as rcon:
            response = await rcon("showplayers")
            print(f"Server {server['ip']}:\n{response}")
    except Exception as e:
        print(f"Error connecting to server {server['ip']}: {e}")

async def main():
    tasks = [test_rcon(server) for server in SERVERS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
