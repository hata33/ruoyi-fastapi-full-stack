import subprocess
import time
import os
import requests

os.chdir(r'D:\Project\AASelf\RuoYi-FastAPI\backend')

print("=== Step 1: Kill existing process on port 9099 ===")
try:
    result = subprocess.run(
        ['powershell', '-Command',
         "Get-NetTCPConnection -LocalPort 9099 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        pid = int(result.stdout.strip())
        print(f"Killing process {pid}")
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
    else:
        print("Port 9099 is free")
except:
    print("Could not check port")

print("\n=== Step 2: Start server ===")
log_file = open('server_output.log', 'w')
server_proc = subprocess.Popen(
    ['python', 'start_server.py'],
    stdout=log_file,
    stderr=subprocess.STDOUT
)

print(f"Server started with PID: {server_proc.pid}")

print("\n=== Step 3: Wait for server to start ===")
time.sleep(15)

print("\n=== Step 4: Check if server is running ===")
if server_proc.poll() is None:
    print("Server process is running")
else:
    print(f"Server exited with code: {server_proc.returncode}")
    log_file.close()
    with open('server_output.log', 'r', encoding='utf-8', errors='ignore') as f:
        print("=== Server Output ===")
        print(f.read()[-2000:])  # Last 2000 chars
    exit(1)

print("\n=== Step 5: Test API ===")
try:
    # Test login
    response = requests.post(
        "http://localhost:9099/login",
        data={"username": "admin", "password": "admin123", "code": "1234"}
    )
    print(f"Login status: {response.status_code}")
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"Got token: {token[:30]}...")

        # Test create conversation
        headers = {"Authorization": f"Bearer {token}"}
        conv_response = requests.post(
            "http://localhost:9099/api/chat/conversations",
            headers=headers,
            json={"title": "测试会话", "modelId": "deepseek-chat"}
        )
        print(f"\nCreate conversation status: {conv_response.status_code}")
        print(f"Response: {conv_response.text[:500]}")
    else:
        print(f"Login failed: {response.text[:200]}")
except Exception as e:
    print(f"Test error: {e}")

print("\n=== Step 6: Keep server running ===")
print("Press Ctrl+C to stop the server")
try:
    server_proc.wait()
except KeyboardInterrupt:
    print("\nStopping server...")
    server_proc.terminate()
