import asyncio
import traceback
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .http_utils import http_get

roblox_user_id_search = on_keyword(["用户ID搜索", "/用户ID搜索"], priority=5, block=True)

async def get_user_details(user_id):
    url = f"https://users.roblox.com/v1/users/{user_id}"
    try:
        return await http_get(url)
    except:
        return None

async def get_user_status(user_id):
    url = f"https://presence.roblox.com/v1/presence/users"
    try:
        from .http_utils import http_post
        data = await http_post(url, data={"userIds": [user_id]})
        if data.get("userPresences"):
            return data["userPresences"][0]
    except:
        pass
    return None

async def get_groups(user_id):
    url = f"https://groups.roblox.com/v1/users/{user_id}/groups/roles?limit=10"
    try:
        data = await http_get(url)
        return data.get("data", [])
    except:
        return []

async def get_friend_count(user_id):
    url = f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
    try:
        data = await http_get(url)
        return data.get("count", 0)
    except:
        return 0

async def get_follower_count(user_id):
    url = f"https://friends.roblox.com/v1/users/{user_id}/followers/count"
    try:
        data = await http_get(url)
        return data.get("count", 0)
    except:
        return 0

async def get_following_count(user_id):
    url = f"https://friends.roblox.com/v1/users/{user_id}/followings/count"
    try:
        data = await http_get(url)
        return data.get("count", 0)
    except:
        return 0

async def get_avatar_url(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png"
    try:
        data = await http_get(url)
        if data.get("data") and len(data["data"]) > 0:
            return data["data"][0].get("imageUrl", "")
    except:
        pass
    return ""

async def get_avatar_headshot_url(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
    try:
        data = await http_get(url)
        if data.get("data") and len(data["data"]) > 0:
            return data["data"][0].get("imageUrl", "")
    except:
        pass
    return ""

@roblox_user_id_search.handle()
async def handle_user_id_search(event: Event):
    raw_text = str(event.get_message()).strip()
    uid_str = raw_text.replace("用户ID搜索", "").replace("/用户ID搜索", "").strip()
    
    if not uid_str or not uid_str.isdigit():
        await roblox_user_id_search.finish("请输入有效的用户ID（纯数字），例：用户ID搜索 123456789")
    uid = int(uid_str)
    
    await roblox_user_id_search.send("稍等，正在查询Roblox用户信息...")
    total_start = time.time()
    
    try:
        details = await get_user_details(uid)
        if not details:
            await roblox_user_id_search.finish("未找到该用户，请检查用户ID是否正确！")
        
        raw_name = details.get("name", "")
        display_name = details.get("displayName", raw_name)
        created = details.get("created", "")
        is_banned = details.get("isBanned", False)
        description = details.get("description", "")
        
        status_task = asyncio.create_task(get_user_status(uid))
        groups_task = asyncio.create_task(get_groups(uid))
        friend_count_task = asyncio.create_task(get_friend_count(uid))
        follower_count_task = asyncio.create_task(get_follower_count(uid))
        following_count_task = asyncio.create_task(get_following_count(uid))
        avatar_url_task = asyncio.create_task(get_avatar_url(uid))
        headshot_url_task = asyncio.create_task(get_avatar_headshot_url(uid))
        
        await asyncio.gather(
            status_task, groups_task, friend_count_task,
            follower_count_task, following_count_task,
            avatar_url_task, headshot_url_task
        )
        
        status = status_task.result()
        groups = groups_task.result()
        friend_count = friend_count_task.result()
        follower_count = follower_count_task.result()
        following_count = following_count_task.result()
        avatar_url = avatar_url_task.result()
        headshot_url = headshot_url_task.result()
        
        online_status = "离线"
        location = "无"
        if status:
            if status.get("userPresenceType") == 2:
                online_status = "在线"
            elif status.get("userPresenceType") == 3:
                online_status = "游戏中"
            elif status.get("userPresenceType") == 4:
                online_status = "工作室中"
            if status.get("lastLocation"):
                location = status["lastLocation"]
        
        created_date = ""
        age_info = ""
        if created:
            created_date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
            delta = relativedelta(datetime.now(), datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ"))
            total_days = (datetime.now() - datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ")).days
            age_info = f"{delta.years}年{delta.months}月{delta.days}天（共{total_days}天）"
        
        output = f"📄 Roblox 用户信息查询（ID）\n\n"
        output += f"👤 用户名：{raw_name}\n"
        output += f"🏷️ 展示名：{display_name}\n"
        output += f"🆔 用户ID：{uid}\n"
        if created_date:
            output += f"📅 注册日期：{created_date}\n"
            output += f"⏳ 注册时长：{age_info}\n"
        output += f"👥 好友：{friend_count} | 关注：{following_count} | 粉丝：{follower_count}\n"
        output += f"🟢 在线状态：{online_status}\n"
        output += f"📍 当前位置：{location}\n"
        output += f"🚫 账号封禁：{'是' if is_banned else '否'}\n"
        
        if description:
            output += f"\n📝 用户简介：\n{description[:200]}{'......' if len(description)>200 else ''}\n"
        
        if groups:
            output += f"\n🏠 已加入群组(前10个)：\n"
            for idx, group in enumerate(groups, 1):
                group_name = group.get("group", {}).get("name", "未知")
                role = group.get("role", {}).get("name", "未知")
                group_id = group.get("group", {}).get("id", 0)
                output += f"{idx}) {group_name}｜职位:{role}\n"
                output += f"   群组ID：{group_id}\n"
        
        messages = []
        if headshot_url:
            try:
                import requests
                response = requests.get(headshot_url, timeout=5)
                if response.status_code == 200:
                    messages.append(MessageSegment.image(response.content))
            except:
                pass
        
        if avatar_url:
            try:
                import requests
                response = requests.get(avatar_url, timeout=5)
                if response.status_code == 200:
                    messages.append(MessageSegment.image(response.content))
            except:
                pass
        
        messages.append(output)
        
        await roblox_user_id_search.finish(messages)

    except ActionFailed:
        await roblox_user_id_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except FinishedException:
        raise
    except Exception as e:
        print("[用户ID搜索错误]", traceback.format_exc())
        await roblox_user_id_search.finish(f"搜索失败：{str(e)}")
    finally:
        print(f"[DEBUG] 用户ID搜索耗时: {time.time()-total_start:.2f}s")
