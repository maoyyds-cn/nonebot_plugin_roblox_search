import asyncio
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event
from nonebot.exception import ActionFailed
from .http_utils import http_get

roblox_get_friends = on_keyword(["/获取好友列表","获取好友列表"], priority=5, block=True)

async def get_friends(uid, limit=10):
    url = f"https://friends.roblox.com/v1/users/{uid}/friends?limit={limit}"
    try:
        data = await http_get(url)
        return data.get("data", [])
    except Exception:
        return []

@roblox_get_friends.handle()
async def handle_get_friends(event: Event):
    raw_text = str(event.get_message()).strip()
    uid_str = raw_text.replace("/获取好友列表", "").strip()
    
    if not uid_str or not uid_str.isdigit():
        await roblox_get_friends.finish("请输入有效的用户ID（纯数字），例：/获取好友列表 123456789")
    uid = int(uid_str)
    
    await roblox_get_friends.send("稍等，正在获取好友列表...")
    total_start = time.time()
    
    try:
        friends = await get_friends(uid, 10)
        if not friends:
            await roblox_get_friends.finish("未找到该用户的好友列表或用户ID不存在！")
        
        output = f"👥 用户ID {uid} 的好友列表（前10个）\n\n"
        for idx, friend in enumerate(friends, 1):
            name = friend.get("name", "未知")
            display_name = friend.get("displayName", "未知")
            friend_id = friend.get("id", 0)
            output += f"{idx}. {name}（{display_name}）\n🆔 ID：{friend_id}\n\n"
        
        await roblox_get_friends.finish(output.strip())

    except ActionFailed:
        await roblox_get_friends.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[获取好友列表错误]", traceback.format_exc())
        await roblox_get_friends.finish(f"获取失败：{str(e)}")
    finally:
        print(f"[DEBUG] 获取好友列表耗时: {time.time()-total_start:.2f}s")
