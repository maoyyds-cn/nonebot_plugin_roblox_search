import json
import time
import asyncio
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "https://www.roblox.com",
    "Referer": "https://www.roblox.com/",
}

TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

async def http_get(url, headers=None, retries=MAX_RETRIES):
    all_headers = headers or HEADERS.copy()
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=all_headers, timeout=TIMEOUT)
            if response.status_code == 429:
                if attempt < retries - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"[HTTP] 429 Too Many Requests, 第{attempt+1}次重试，等待{wait_time}秒...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"[HTTP GET Error] {url}: 429 Too Many Requests (已重试{retries}次)")
                    return {}
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < retries - 1:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"[HTTP] 请求失败，第{attempt+1}次重试: {str(e)}，等待{wait_time}秒...")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"[HTTP GET Error] {url}: {str(e)}")
                return {}

async def http_post(url, data=None, headers=None, retries=MAX_RETRIES):
    all_headers = headers or HEADERS.copy()
    if data:
        all_headers["Content-Type"] = "application/json"
    
    for attempt in range(retries):
        try:
            if data:
                response = requests.post(url, json=data, headers=all_headers, timeout=TIMEOUT)
            else:
                response = requests.post(url, headers=all_headers, timeout=TIMEOUT)
            
            if response.status_code == 429:
                if attempt < retries - 1:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    print(f"[HTTP] 429 Too Many Requests, 第{attempt+1}次重试，等待{wait_time}秒...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"[HTTP POST Error] {url}: 429 Too Many Requests (已重试{retries}次)")
                    return {}
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt < retries - 1:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"[HTTP] 请求失败，第{attempt+1}次重试: {str(e)}，等待{wait_time}秒...")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"[HTTP POST Error] {url}: {str(e)}")
                return {}
