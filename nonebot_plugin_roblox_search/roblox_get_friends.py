import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .render_utils import rich_text_to_image
from .http_utils import http_get, http_post

roblox_get_friends = on_keyword(["/获取好友列表","获取好友列表"], priority=5, block=True)

async def get_friend_list(uid):
    url = f"https://friends.roblox.com/v1/users/{uid}/friends?limit=10"
    try:
        data = await http_get(url)
        return data.get("data", [])
    except Exception:
        return []

async def get_user_basic_info(uids):
    url = "https://users.roblox.com/v1/users/usernames"
    payload = {"userIds": uids, "excludeBannedUsers": False}
    try:
        data = await http_post(url, data=payload)
        return {item["id"]: item for item in data.get("data", [])}
    except Exception:
        return {}

@roblox_get_friends.handle()
async def handle_get_friends(event: Event):
    raw_text = str(event.get_message()).strip()
    
    keywords = ["/获取好友列表", "获取好友列表"]
    uid_str = None
    for kw in keywords:
        if raw_text.startswith(kw):
            uid_str = raw_text[len(kw):].strip()
            break
    
    if not uid_str or not uid_str.isdigit():
        await roblox_get_friends.finish("请输入有效的Roblox用户ID（纯数字），例：/获取好友列表 123456789")
    uid = int(uid_str)
    
    await roblox_get_friends.send("稍等，正在获取好友列表...")
    total_start = time.time()
    
    try:
        friend_list = await get_friend_list(uid)
        if not friend_list:
            await roblox_get_friends.finish("该用户暂无好友，或无法获取好友列表！")
        
        friend_list = friend_list[:10]
        
        friend_uids = [f.get("id", 0) for f in friend_list]
        friend_info_map = await get_user_basic_info(friend_uids)
        
        output = f"👥 用户ID {uid} 的好友列表（前10个）：\n\n"
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
        
        try:
            img_bytes = await rich_text_to_image(output.strip(), "👥 Roblox 好友列表")
            await roblox_get_friends.finish(MessageSegment.image(img_bytes))
        except Exception as e:
            print(f"[好友列表渲染错误] {e}")
            await roblox_get_friends.finish(output.strip())

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_get_friends.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[获取好友列表错误]", traceback.format_exc())
        await roblox_get_friends.finish(f"获取失败：{str(e)}")
    finally:
        print(f"[DEBUG] 获取好友列表耗时: {time.time()-total_start:.2f}s")
