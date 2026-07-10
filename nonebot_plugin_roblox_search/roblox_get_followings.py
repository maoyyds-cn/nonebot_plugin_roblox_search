import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException

HEADERS = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
TIMEOUT = 30

# 触发关键词：/获取关注列表
roblox_get_followings = on_keyword(["/获取关注列表","获取关注列表"], priority=5, block=True)

async def curl_request(method, url, data=None, headers=None):
    cmd = ["curl", "-s", "-X", method, "--max-time", str(TIMEOUT)]
    if data:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    for h in (headers or HEADERS):
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
    return json.loads(stdout.decode()) if stdout else {}

async def get_following_list(uid):
    """获取用户关注列表"""
    url = f"https://friends.roblox.com/v1/users/{uid}/followings?limit=10"  # 最多10个
    try:
        data = await curl_request("GET", url)
        return data.get("data", [])
    except Exception:
        return []

async def get_user_basic_info(uids):
    """批量获取用户基础信息"""
    url = "https://users.roblox.com/v1/users/usernames"
    payload = {"userIds": uids, "excludeBannedUsers": False}
    try:
        data = await curl_request("POST", url, data=payload)
        return {item["id"]: item for item in data.get("data", [])}
    except Exception:
        return {}

@roblox_get_followings.handle()
async def handle_get_followings(event: Event):
    raw_text = str(event.get_message()).strip()
    
    keywords = ["/获取关注列表", "获取关注列表"]
    uid_str = None
    for kw in keywords:
        if raw_text.startswith(kw):
            uid_str = raw_text[len(kw):].strip()
            break
    
    if not uid_str or not uid_str.isdigit():
        await roblox_get_followings.finish("请输入有效的Roblox用户ID（纯数字），例：/获取关注列表 123456789")
    uid = int(uid_str)
    
    await roblox_get_followings.send("稍等，正在获取关注列表...")
    total_start = time.time()
    
    try:
        following_list = await get_following_list(uid)
        if not following_list:
            await roblox_get_followings.finish("该用户暂无关注，或无法获取关注列表！")
        
        following_list = following_list[:10]
        
        following_uids = [f.get("id", 0) for f in following_list]
        following_info_map = await get_user_basic_info(following_uids)
        
        output = f"🔍 用户ID {uid} 的关注列表（前10个）：\n\n"
        for idx, following in enumerate(following_list):
            following_id = following.get("id", 0)
            following_info = following_info_map.get(following_id, {})
            username = following_info.get("name", "未知")
            display_name = following_info.get("displayName", "未知")
            followed_at = following.get("created", "").split("T")[0] if following.get("created") else "未知时间"
            
            output += (
                f"【{idx+1}】\n"
                f"用户ID：{following_id}\n"
                f"用户名：{username}\n"
                f"展示名：{display_name}\n"
                f"关注时间：{followed_at}\n\n"
            )
        
        await roblox_get_followings.finish(output.strip())

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_get_followings.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[获取关注列表错误]", traceback.format_exc())
        await roblox_get_followings.finish(f"获取失败：{str(e)}")
    finally:
        print(f"[DEBUG] 获取关注列表耗时: {time.time()-total_start:.2f}s")