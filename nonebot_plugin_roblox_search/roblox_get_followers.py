import asyncio
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, MessageSegment
from nonebot.exception import ActionFailed
from .http_utils import http_get
from .render_utils import text_to_image

roblox_get_followers = on_keyword(["/获取粉丝列表","获取粉丝列表"], priority=5, block=True)

async def get_followers(uid, limit=10):
    url = f"https://friends.roblox.com/v1/users/{uid}/followers?limit={limit}"
    try:
        data = await http_get(url)
        return data.get("data", [])
    except Exception:
        return []

@roblox_get_followers.handle()
async def handle_get_followers(event: Event):
    raw_text = str(event.get_message()).strip()
    uid_str = raw_text.replace("/获取粉丝列表", "").strip()
    
    if not uid_str or not uid_str.isdigit():
        await roblox_get_followers.finish("请输入有效的用户ID（纯数字），例：/获取粉丝列表 123456789")
    uid = int(uid_str)
    
    await roblox_get_followers.send("稍等，正在获取粉丝列表...")
    total_start = time.time()
    
    try:
        followers = await get_followers(uid, 10)
        if not followers:
            await roblox_get_followers.finish("未找到该用户的粉丝列表或用户ID不存在！")
        
        output = ""
        for idx, follower in enumerate(followers, 1):
            name = follower.get("name", "未知")
            display_name = follower.get("displayName", "未知")
            follower_id = follower.get("id", 0)
            output += f"{idx}. {name}（{display_name}）\n🆔 ID：{follower_id}\n\n"
        
        img_bytes = await text_to_image(output.strip(), title=f"❤️ 用户ID {uid} 的粉丝列表（前10个）")
        await roblox_get_followers.finish(MessageSegment.image(img_bytes))

    except ActionFailed:
        await roblox_get_followers.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[获取粉丝列表错误]", traceback.format_exc())
        await roblox_get_followers.finish(f"获取失败：{str(e)}")
    finally:
        print(f"[DEBUG] 获取粉丝列表耗时: {time.time()-total_start:.2f}s")
