import json
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

TIMEOUT = 30

async def http_get(url, headers=None):
    try:
        all_headers = headers or HEADERS
        response = requests.get(url, headers=all_headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[HTTP GET Error] {url}: {str(e)}")
        return {}

async def http_post(url, data=None, headers=None):
    try:
        all_headers = headers or HEADERS
        if data:
            all_headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=all_headers, timeout=TIMEOUT)
        else:
            response = requests.post(url, headers=all_headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[HTTP POST Error] {url}: {str(e)}")
        return {}
