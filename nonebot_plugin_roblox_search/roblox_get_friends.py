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

# 触发关键词：/获取好友列表
roblox_get_friends = on_keyword(["/获取好友列表","获取好友列表"], priority=5, block=True)

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

async def get_friend_list(uid):
    """获取用户好友列表"""
    url = f"https://friends.roblox.com/v1/users/{uid}/friends?limit=10"  # 最多10个
    try:
        data = await curl_request("GET", url)
        return data.get("data", [])
    except Exception:
        return []

async def get_user_basic_info(uids):
    """批量获取用户基础信息（用户名/显示名）"""
    url = "https://users.roblox.com/v1/users/usernames"
    payload = {"userIds": uids, "excludeBannedUsers": False}
    try:
        data = await curl_request("POST", url, data=payload)
        return {item["id"]: item for item in data.get("data", [])}
    except Exception:
        return {}

@roblox_get_friends.handle()
async def handle_get_friends(event: Event):
    # 提取用户ID
    raw_text = str(event.get_message()).strip()
    uid_str = raw_text.replace("/获取好友列表", "").strip()
    
    if not uid_str or not uid_str.isdigit():
        await roblox_get_friends.finish("请输入有效的Roblox用户ID（纯数字），例：/获取好友列表 123456789")
    uid = int(uid_str)
    
    await roblox_get_friends.send("稍等，正在获取好友列表...")
    total_start = time.time()
    
    try:
        # 获取好友列表
        friend_list = await get_friend_list(uid)
        if not friend_list:
            await roblox_get_friends.finish("该用户暂无好友，或无法获取好友列表！")
        
        # 批量获取好友基础信息
        friend_uids = [f.get("id", 0) for f in friend_list]
        friend_info_map = await get_user_basic_info(friend_uids)
        
        # 组装结果
        output = f"👥 用户ID {uid} 的好友列表（共{len(friend_list)}个）：\n\n"
        for idx, friend in enumerate(friend_list):
            friend_id = friend.get("id", 0)
            friend_info = friend_info_map.get(friend_id, {})
            username = friend_info.get("name", "未知")
            display_name = friend_info.get("displayName", "未知")
            mutual = "✅ 互关" if friend.get("isMutualFriend", False) else "❌ 单向"
            
            output += (
                f"【{idx+1}】\n"
                f"用户ID：{friend_id}\n"
                f"用户名：{username}\n"
                f"展示名：{display_name}\n"
                f"关系：{mutual}\n\n"
            )
        
        await roblox_get_friends.finish(output.strip())

    except ActionFailed:
        raise
    except Exception as e:
        print("[获取好友列表错误]", traceback.format_exc())
        await roblox_get_friends.finish(f"获取失败：{str(e)}")
    finally:
        print(f"[DEBUG] 获取好友列表耗时: {time.time()-total_start:.2f}s")