import asyncio
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
}

TIMEOUT = 30

async def curl_request(method, url, data=None, headers=None):
    cmd = ["curl", "-s", "-X", method, "--max-time", str(TIMEOUT)]
    
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    
    all_headers = headers or HEADERS
    if isinstance(all_headers, dict):
        for key, value in all_headers.items():
            cmd += ["-H", f"{key}: {value}"]
    else:
        for h in all_headers:
            cmd += ["-H", h]
    
    cmd.append(url)
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"curl 失败: {stderr.decode()}")
    return json.loads(stdout.decode())

async def http_get(url, headers=None):
    return await curl_request("GET", url, headers=headers)

async def http_post(url, data=None, headers=None):
    return await curl_request("POST", url, data=data, headers=headers)
