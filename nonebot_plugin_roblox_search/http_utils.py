import json
import aiohttp

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

TIMEOUT = 30

_session = None

async def get_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT), headers=HEADERS)
    return _session

async def http_request(method: str, url: str, data=None, headers=None) -> dict:
    all_headers = HEADERS.copy()
    if headers:
        all_headers.update(headers)
    
    session = await get_session()
    
    async with session.request(method, url, json=data, headers=all_headers) as response:
        try:
            body = await response.json()
        except:
            try:
                body = await response.text()
            except:
                body = {}
        
        if response.status != 200:
            error_info = f"HTTP请求失败: {response.status}"
            if isinstance(body, dict) and body.get("errors"):
                error_info += f" - {json.dumps(body.get('errors'))}"
            elif isinstance(body, str):
                error_info += f" - {body[:200]}"
            raise Exception(error_info)
        
        return body if isinstance(body, dict) else {}

async def http_get(url: str, headers=None) -> dict:
    return await http_request("GET", url, headers=headers)

async def http_post(url: str, data=None, headers=None) -> dict:
    return await http_request("POST", url, data=data, headers=headers)
