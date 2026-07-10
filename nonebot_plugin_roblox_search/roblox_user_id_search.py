import asyncio
import traceback
import time
from datetime import datetime
from dateutil import relativedelta
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .http_utils import http_get, http_post
from .render_utils import text_to_image

roblox_user_id_search = on_keyword(["/用户ID搜索","用户ID搜索"], priority=5, block=True)

async def get_user_info(uid):
    url = f"https://users.roblox.com/v1/users/{uid}"
    return await http_get(url)

async def get_user_premium(uid):
    url = f"https://premiumfeatures.roblox.com/v1/users/{uid}/validate-membership"
    try:
        return (await http_get(url)).get("isValid", False)
    except Exception:
        return False

async def get_avatar_img_url(uid):
    url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png&isCircular=false"
    try:
        data = await http_get(url)
        return data.get("data", [{}])[0].get("imageUrl", "")
    except Exception:
        return ""

async def get_user_presence(uids):
    url = "https://presence.roblox.com/v1/presence/users"
    try:
        data = await http_post(url, data={"userIds": uids})
        return data.get("userPresences", [{}])[0]
    except Exception:
        return {}

def calc_register_time(created_str):
    if not created_str:
        return "未知", "未知"
    create_time = datetime.fromisoformat(created_str.replace("Z", ""))
    now_utc = datetime.utcnow()
    diff = relativedelta.relativedelta(now_utc, create_time)
    delta_day = (now_utc - create_time).days
    time_text = f"{diff.years}年{diff.months}月{diff.days}天（共{delta_day}天）"
    date_short = create_time.strftime("%Y-%m-%d")
    return date_short, time_text

@roblox_user_id_search.handle()
async def handle_user_id_search(event: Event):
    raw_text = str(event.get_message()).strip()
    uid_str = raw_text.replace("/用户ID搜索", "").strip()
    
    if not uid_str or not uid_str.isdigit():
        await roblox_user_id_search.finish("请输入有效的Roblox用户ID（纯数字），例：/用户ID搜索 123456789")
    uid = int(uid_str)
    
    await roblox_user_id_search.send("稍等，正在查询用户信息...")
    total_start = time.time()
    
    try:
        tasks = [
            get_user_info(uid),
            get_user_premium(uid),
            get_avatar_img_url(uid),
            get_user_presence([uid])
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        user_info, is_premium, avatar_url, presence = results
        
        if isinstance(user_info, Exception) or not user_info:
            await roblox_user_id_search.finish("未找到该用户ID对应的信息！")
        if isinstance(is_premium, Exception):
            is_premium = False
        if isinstance(avatar_url, Exception):
            avatar_url = ""
        if isinstance(presence, Exception):
            presence = {}
        
        display_name = user_info.get("displayName", "未知")
        raw_name = user_info.get("name", "未知")
        desc = user_info.get("description", "").strip() or "无简介"
        created = user_info.get("created", "")
        is_banned = user_info.get("isBanned", False)
        reg_date, reg_full_time = calc_register_time(created)
        
        online_status = "离线"
        device = "无"
        presence_type = presence.get("userPresenceType", 0)
        location = presence.get("lastLocation", "")
        if presence_type == 2:
            online_status = "在线(游戏中)"
            device = location if location else "未知游戏"
        elif presence_type == 1:
            online_status = "网页在线"
            device = "Roblox网页端"
        
        premium_text = "是" if is_premium else "否"
        
        output = (
            f"🆔 用户ID：{uid}\n"
            f"👤 用户名：{raw_name}\n"
            f"🏷️ 展示名：{display_name}\n"
            f"📅 注册日期：{reg_date}\n"
            f"⏳ 注册时长：{reg_full_time}\n"
            f"💎 Premium会员：{premium_text}\n"
            f"👥 在线状态：{online_status}\n"
            f"📍 当前位置：{device}\n"
            f"🚫 账号封禁：{'是' if is_banned else '否'}\n\n"
            f"📝 简介：\n{desc[:300]}{'......' if len(desc)>300 else ''}"
        )
        
        img_bytes = await text_to_image(output, title="📄 Roblox 用户ID查询结果", avatar_url=avatar_url)
        await roblox_user_id_search.finish(MessageSegment.image(img_bytes))

    except ActionFailed:
        await roblox_user_id_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[用户ID搜索错误]", traceback.format_exc())
        await roblox_user_id_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 用户ID搜索耗时: {time.time()-total_start:.2f}s")
