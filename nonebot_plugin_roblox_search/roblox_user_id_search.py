import asyncio
import json
import traceback
import time
from datetime import datetime
from dateutil import relativedelta
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed

HEADERS = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
TIMEOUT = 30

# 触发关键词：/用户ID搜索
roblox_user_id_search = on_keyword(["/用户ID搜索","用户ID搜索"], priority=5, block=True)

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

async def get_user_info(uid):
    """根据UID获取用户信息"""
    url = f"https://users.roblox.com/v1/users/{uid}"
    return await curl_request("GET", url)

async def get_user_premium(uid):
    """判断Premium会员"""
    url = f"https://premiumfeatures.roblox.com/v1/users/{uid}/validate-membership"
    try:
        return (await curl_request("GET", url)).get("isValid", False)
    except Exception:
        return False

async def get_avatar_img_url(uid):
    """获取头像链接"""
    url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png&isCircular=false"
    try:
        data = await curl_request("GET", url)
        return data.get("data", [{}])[0].get("imageUrl", "")
    except Exception:
        return ""

async def get_user_presence(uids):
    """获取在线状态"""
    url = "https://presence.roblox.com/v1/presence/users"
    try:
        data = await curl_request("POST", url, data={"userIds": uids})
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
    # 提取用户ID
    raw_text = str(event.get_message()).strip()
    uid_str = raw_text.replace("/用户ID搜索", "").strip()
    
    if not uid_str or not uid_str.isdigit():
        await roblox_user_id_search.finish("请输入有效的Roblox用户ID（纯数字），例：/用户ID搜索 123456789")
    uid = int(uid_str)
    
    await roblox_user_id_search.send("稍等，正在查询用户信息...")
    total_start = time.time()
    
    try:
        # 并发请求数据
        tasks = [
            get_user_info(uid),
            get_user_premium(uid),
            get_avatar_img_url(uid),
            get_user_presence([uid])
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        user_info, is_premium, avatar_url, presence = results
        
        # 异常兜底
        if isinstance(user_info, Exception) or not user_info:
            await roblox_user_id_search.finish("未找到该用户ID对应的信息！")
        if isinstance(is_premium, Exception):
            is_premium = False
        if isinstance(avatar_url, Exception):
            avatar_url = ""
        if isinstance(presence, Exception):
            presence = {}
        
        # 解析信息
        display_name = user_info.get("displayName", "未知")
        raw_name = user_info.get("name", "未知")
        desc = user_info.get("description", "").strip() or "无简介"
        created = user_info.get("created", "")
        is_banned = user_info.get("isBanned", False)
        reg_date, reg_full_time = calc_register_time(created)
        
        # 在线状态
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
        
        # 会员状态
        premium_text = "是" if is_premium else "否"
        
        # 组装输出
        output = (
            f"📄 Roblox 用户ID查询结果\n"
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
        
        # 发送结果
        if avatar_url:
            msg = MessageSegment.image(avatar_url) + output
        else:
            msg = output
        await roblox_user_id_search.finish(msg)

    except ActionFailed:
        raise
    except Exception as e:
        print("[用户ID搜索错误]", traceback.format_exc())
        await roblox_user_id_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 用户ID搜索耗时: {time.time()-total_start:.2f}s")