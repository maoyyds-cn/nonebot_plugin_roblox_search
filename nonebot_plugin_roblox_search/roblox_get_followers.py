import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed

HEADERS = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
TIMEOUT = 30

# 触发关键词：/获取粉丝列表
roblox_get_followers = on_keyword(["/获取粉丝列表","获取粉丝列表"], priority=5, block=True)

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

async def get_follower_list(uid):
    """获取用户粉丝列表"""
    url = f"https://friends.roblox.com/v1/users/{uid}/followers?limit=10"  # 最多10个
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

@roblox_get_followers.handle()
async def handle_get_followers(event: Event):
    # 提取用户ID
    raw_text = str(event.get_message()).strip()
    uid_str = raw_text.replace("/获取粉丝列表", "").strip()
    
    if not uid_str or not uid_str.isdigit():
        await roblox_get_followers.finish("请输入有效的Roblox用户ID（纯数字），例：/获取粉丝列表 123456789")
    uid = int(uid_str)
    
    await roblox_get_followers.send("稍等，正在获取粉丝列表...")
    total_start = time.time()
    
    try:
        # 获取粉丝列表
        follower_list = await get_follower_list(uid)
        if not follower_list:
            await roblox_get_followers.finish("该用户暂无粉丝，或无法获取粉丝列表！")
        
        # 批量获取粉丝基础信息
        follower_uids = [f.get("id", 0) for f in follower_list]
        follower_info_map = await get_user_basic_info(follower_uids)
        
        # 组装结果
        output = f"🌟 用户ID {uid} 的粉丝列表（共{len(follower_list)}个）：\n\n"
        for idx, follower in enumerate(follower_list):
            follower_id = follower.get("id", 0)
            follower_info = follower_info_map.get(follower_id, {})
            username = follower_info.get("name", "未知")
            display_name = follower_info.get("displayName", "未知")
            followed_at = follower.get("created", "").split("T")[0] if follower.get("created") else "未知时间"
            
            output += (
                f"【{idx+1}】\n"
                f"用户ID：{follower_id}\n"
                f"用户名：{username}\n"
                f"展示名：{display_name}\n"
                f"关注时间：{followed_at}\n\n"
            )
        
        await roblox_get_followers.finish(output.strip())

    except ActionFailed:
        raise
    except Exception as e:
        print("[获取粉丝列表错误]", traceback.format_exc())
        await roblox_get_followers.finish(f"获取失败：{str(e)}")
    finally:
        print(f"[DEBUG] 获取粉丝列表耗时: {time.time()-total_start:.2f}s")