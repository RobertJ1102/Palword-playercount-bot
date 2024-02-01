import subprocess

# RCON Server Configurations
SERVERS = [
    {"address": "localhost:25575", "password": "ojii0hoajkos"},
    # Add more servers as needed
]

# Path to rcon.exe
RCON_EXE_PATH = "C:\\Discord Bots\\Palword-playercount-bot\\rcon\\rcon.exe"

def test_rcon(server):
    try:
        # Constructing the command
        command = [RCON_EXE_PATH, "-a", server['address'], "-p", server['password'], "info"]
        
        # Running the command
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Checking and printing the output and error
        if result.stdout:
            res = result.stdout
            print(res)
        if result.stderr:
            print(f"Server {server['address']} Error:\n{result.stderr}")
    except Exception as e:
        print(f"Error connecting to server {server['address']}: {e}")

def main():
    for server in SERVERS:
        test_rcon(server)

if __name__ == "__main__":
    main()
