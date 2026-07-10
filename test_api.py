import subprocess
import json

cmd = [
    'curl.exe', '-s', '-X', 'POST',
    '-H', 'Content-Type: application/json',
    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    '-d', '{"usernames":["maochina_4"],"excludeBannedUsers":false}',
    'https://users.roblox.com/v1/usernames/users'
]

print(f"Command: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"Return code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")
