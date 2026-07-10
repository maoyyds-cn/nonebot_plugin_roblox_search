import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .render_utils import rich_text_to_image
from .http_utils import http_get, http_post

roblox_get_followers = on_keyword(["/获取粉丝列表","获取粉丝列表"], priority=5, block=True)

async def get_follower_list(uid):
    url = f"https://friends.roblox.com/v1/users/{uid}/followers?limit=10"
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

@roblox_get_followers.handle()
async def handle_get_followers(event: Event):
    raw_text = str(event.get_message()).strip()
    
    keywords = ["/获取粉丝列表", "获取粉丝列表"]
    uid_str = None
    for kw in keywords:
        if raw_text.startswith(kw):
            uid_str = raw_text[len(kw):].strip()
            break
    
    if not uid_str or not uid_str.isdigit():
        await roblox_get_followers.finish("请输入有效的Roblox用户ID（纯数字），例：/获取粉丝列表 123456789")
    uid = int(uid_str)
    
    await roblox_get_followers.send("稍等，正在获取粉丝列表...")
    total_start = time.time()
    
    try:
        follower_list = await get_follower_list(uid)
        if not follower_list:
            await roblox_get_followers.finish("该用户暂无粉丝，或无法获取粉丝列表！")
        
        follower_list = follower_list[:10]
        
        follower_uids = [f.get("id", 0) for f in follower_list]
        follower_info_map = await get_user_basic_info(follower_uids)
        
        output = f"🌟 用户ID {uid} 的粉丝列表（前10个）：\n\n"
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
        
        try:
            img_bytes = await rich_text_to_image(output.strip(), "🌟 Roblox 粉丝列表")
            await roblox_get_followers.finish(MessageSegment.image(img_bytes))
        except Exception as e:
            print(f"[粉丝列表渲染错误] {e}")
            await roblox_get_followers.finish(output.strip())

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_get_followers.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[获取粉丝列表错误]", traceback.format_exc())
        await roblox_get_followers.finish(f"获取失败：{str(e)}")
    finally:
        print(f"[DEBUG] 获取粉丝列表耗时: {time.time()-total_start:.2f}s")
