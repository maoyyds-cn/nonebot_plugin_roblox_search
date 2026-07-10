import asyncio
import json
import traceback
import time
from datetime import datetime
from dateutil import relativedelta
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException

HEADERS = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
TIMEOUT = 30

# 使用 on_keyword，匹配多个关键词（无论是否带斜杠）
roblox_search = on_keyword(["用户名搜索","/用户名搜索", "roblox查询", "查roblox"], priority=5, block=True)

async def curl_request(method, url, data=None, headers=None):
    """使用 curl 执行 HTTP 请求，返回 JSON 数据"""
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
    return json.loads(stdout.decode())

async def username_to_uid(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": False}
    data = await curl_request("POST", url, data=payload)
    if not data.get("data"):
        return None
    return data["data"][0]["id"]

async def get_user_info(uid):
    url = f"https://users.roblox.com/v1/users/{uid}"
    return await curl_request("GET", url)

async def get_user_presence(uids):
    url = "https://presence.roblox.com/v1/presence/users"
    payload = {"userIds": uids}
    try:
        data = await curl_request("POST", url, data=payload)
        presences = data.get("userPresences", [])
        return presences[0] if presences else {}
    except Exception:
        return {}

async def get_count(uid):
    friend_url = f"https://friends.roblox.com/v1/users/{uid}/friends/count"
    follower_url = f"https://friends.roblox.com/v1/users/{uid}/followers/count"
    following_url = f"https://friends.roblox.com/v1/users/{uid}/followings/count"
    async def fetch(url):
        try:
            data = await curl_request("GET", url)
            return data.get("count", 0)
        except Exception:
            return 0
    friends, followers, following = await asyncio.gather(fetch(friend_url), fetch(follower_url), fetch(following_url))
    return friends, followers, following

async def get_user_groups(uid):
    url = f"https://groups.roblox.com/v1/users/{uid}/groups/roles"
    try:
        data = await curl_request("GET", url)
        return data.get("data", [])
    except Exception:
        return []

async def get_avatar_img_url(uid):
    url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png&isCircular=false"
    try:
        data = await curl_request("GET", url)
        thumb_data = data.get("data", [])
        if not thumb_data:
            return ""
        return thumb_data[0].get("imageUrl", "")
    except Exception:
        return ""

def calc_register_time(created_str):
    create_time = datetime.fromisoformat(created_str.replace("Z", ""))
    now_utc = datetime.utcnow()
    diff = relativedelta.relativedelta(now_utc, create_time)
    delta_day = (now_utc - create_time).days
    time_text = f"{diff.years}年{diff.months}月{diff.days}天（共{delta_day}天）"
    date_short = create_time.strftime("%Y-%m-%d")
    return date_short, time_text

@roblox_search.handle()
async def handle_search(event: Event):
    # 获取原始消息文本
    raw_msg = event.get_message()
    raw_text = str(raw_msg).strip()
    
    # 去掉关键词前缀（支持多个关键词）
    keywords = ["用户名搜索", "roblox查询", "查roblox"]
    username = None
    for kw in keywords:
        if raw_text.startswith(kw):
            username = raw_text[len(kw):].strip()
            break
    # 如果没有匹配到关键词（理论上不会，因为是 on_keyword 触发），但以防万一
    if username is None:
        # 尝试提取第一个空格后的内容
        parts = raw_text.split(maxsplit=1)
        if len(parts) > 1:
            username = parts[1].strip()
        else:
            username = ""
    
    if not username:
        await roblox_search.finish("请输入Roblox用户名，例：用户名搜索 maochina_4")
    
    await roblox_search.send("稍等，正在查询Roblox用户信息...")
    total_start = time.time()
    try:
        uid = await username_to_uid(username)
        if not uid:
            await roblox_search.finish("未找到该用户，请检查用户名是否正确！")
            return
        tasks = [
            get_user_info(uid),
            get_user_presence([uid]),
            get_count(uid),
            get_user_groups(uid),
            get_avatar_img_url(uid)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        user_info, presence, cnt_data, groups, avatar_url = results
        if isinstance(user_info, Exception):
            print(f"[ERROR] user_info 异常: {user_info}")
            user_info = {}
        if isinstance(presence, Exception):
            presence = {}
        if isinstance(cnt_data, Exception):
            cnt_data = (0, 0, 0)
        if isinstance(groups, Exception):
            groups = []
        if isinstance(avatar_url, Exception):
            avatar_url = ""
        friend_cnt, follower_cnt, follow_cnt = cnt_data

        display_name = user_info.get("displayName", "")
        raw_name = user_info.get("name", "")
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
        group_text = ""
        if groups:
            for idx, g in enumerate(groups[:5]):
                g_name = g["group"]["name"][:20]
                g_id = g["group"]["id"]
                g_role = g["role"]["name"][:15]
                group_text += f"{idx+1}) {g_name}｜职位:{g_role}\n群组ID：{g_id}\n"
        else:
            group_text = "暂无加入任何群组"
        if len(desc) > 300:
            desc = desc[:300] + "......(内容过长已截断)"
        output = (
            f"📄 Roblox 用户信息查询\n"
            f"👤 用户名：{raw_name}\n"
            f"🏷️ 展示名：{display_name}\n"
            f"🆔 用户ID：{uid}\n"
            f"📅 注册日期：{reg_date}\n"
            f"⏳ 注册时长：{reg_full_time}\n"
            f"👥 好友：{friend_cnt} | 关注：{follow_cnt} | 粉丝：{follower_cnt}\n"
            f"🟢 在线状态：{online_status}\n"
            f"📍 当前位置：{device}\n"
            f"🚫 账号封禁：{'是' if is_banned else '否'}\n\n"
            f"📝 用户简介：\n{desc}\n\n"
            f"🏠 已加入群组(前5个)：\n{group_text}"
        )
        if avatar_url:
            msg = MessageSegment.image(avatar_url) + output
        else:
            msg = output
        await roblox_search.finish(msg)

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[Roblox未知错误]", traceback.format_exc())
        await roblox_search.finish(f"查询发生未知错误：{str(e)}")
    finally:
        print(f"[DEBUG] 总查询耗时: {time.time()-total_start:.2f}s")