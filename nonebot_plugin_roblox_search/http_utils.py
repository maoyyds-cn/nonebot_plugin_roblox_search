import json
import asyncio
import re
import time
import os
import urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

TIMEOUT = 30

MAX_CONCURRENT_REQUESTS = 3
request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0


def get_curl_command():
    if os.name == 'nt':
        return "curl.exe"
    else:
        return "curl"


def encode_url(url: str) -> str:
    try:
        parts = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parts.query)
        encoded_query = {}
        for key, values in query.items():
            encoded_query[key] = [urllib.parse.quote(v, safe='') for v in values]
        new_query = urllib.parse.urlencode(encoded_query, doseq=True)
        return urllib.parse.urlunparse(parts._replace(query=new_query))
    except:
        return url


def parse_http_response(raw_response: str):
    lines = raw_response.split('\r\n')
    if not lines:
        lines = raw_response.split('\n')
    
    headers = {}
    body_start = 0
    
    for i, line in enumerate(lines):
        if line == '':
            body_start = i + 1
            break
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    
    body = '\r\n'.join(lines[body_start:])
    
    status_match = re.search(r'HTTP/\d+\.\d+\s+(\d+)', lines[0]) if lines else None
    status_code = int(status_match.group(1)) if status_match else 0
    
    return status_code, headers, body


async def curl_request(url: str, method: str = "GET", data: dict = None, headers: dict = None):
    all_headers = headers or HEADERS
    curl_cmd = get_curl_command()
    curl_args = [curl_cmd, "-s", "-i", "-X", method]
    
    for key, value in all_headers.items():
        curl_args.extend(["-H", f"{key}: {value}"])
    
    if data:
        curl_args.extend(["-d", json.dumps(data)])
    
    encoded_url = encode_url(url)
    curl_args.append(encoded_url)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *curl_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        if process.returncode != 0:
            print(f"[CURL Error] {url}: return code {process.returncode}, stderr: {stderr_str}")
            return 0, {}, {}
        
        status_code, resp_headers, body = parse_http_response(stdout_str)
        
        try:
            json_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            json_data = {}
        
        return status_code, resp_headers, json_data
    
    except Exception as e:
        print(f"[CURL Exception] {url}: {str(e)}")
        return 0, {}, {}


async def http_get(url, headers=None):
    async with request_semaphore:
        for attempt in range(MAX_RETRIES):
            status_code, resp_headers, data = await curl_request(url, "GET", headers=headers)
            
            if status_code == 429:
                retry_after = int(resp_headers.get("Retry-After", 0))
                if retry_after > 0:
                    delay = retry_after
                else:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                
                print(f"[429 Too Many Requests] {url}, retry {attempt + 1}/{MAX_RETRIES}, waiting {delay:.2f}s")
                await asyncio.sleep(delay)
                continue
            
            if status_code == 0:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"[Request Failed] {url}, retry {attempt + 1}/{MAX_RETRIES}, waiting {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
            
            if status_code >= 200 and status_code < 300:
                return data
            
            print(f"[HTTP Error] {url}: status {status_code}")
            return {}
        
        print(f"[Max Retries Exceeded] {url}")
        return {}


async def http_post(url, data=None, headers=None):
    async with request_semaphore:
        for attempt in range(MAX_RETRIES):
            all_headers = headers or HEADERS.copy()
            if data:
                all_headers["Content-Type"] = "application/json"
            
            status_code, resp_headers, resp_data = await curl_request(url, "POST", data, all_headers)
            
            if status_code == 429:
                retry_after = int(resp_headers.get("Retry-After", 0))
                if retry_after > 0:
                    delay = retry_after
                else:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                
                print(f"[429 Too Many Requests] {url}, retry {attempt + 1}/{MAX_RETRIES}, waiting {delay:.2f}s")
                await asyncio.sleep(delay)
                continue
            
            if status_code == 0:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"[Request Failed] {url}, retry {attempt + 1}/{MAX_RETRIES}, waiting {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
            
            if status_code >= 200 and status_code < 300:
                return resp_data
            
            print(f"[HTTP Error] {url}: status {status_code}")
            return {}
        
        print(f"[Max Retries Exceeded] {url}")
        return {}