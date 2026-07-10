import asyncio
import traceback
import time
from datetime import datetime
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .http_utils import http_get

roblox_group_id_search = on_keyword(["/群组ID搜索","群组ID搜索"], priority=5, block=True)

async def get_group_info(gid):
    url = f"https://groups.roblox.com/v1/groups/{gid}"
    return await http_get(url)

async def get_group_icon(gid):
    url = f"https://thumbnails.roblox.com/v1/groups/icons?groupIds={gid}&size=512x512&format=Png&isCircular=false"
    try:
        data = await http_get(url)
        return data.get("data", [{}])[0].get("imageUrl", "")
    except Exception:
        return ""

async def get_group_roles(gid):
    url = f"https://groups.roblox.com/v1/groups/{gid}/roles"
    try:
        data = await http_get(url)
        return data.get("roles", [])
    except Exception:
        return []

@roblox_group_id_search.handle()
async def handle_group_id_search(event: Event):
    raw_text = str(event.get_message()).strip()
    gid_str = raw_text.replace("/群组ID搜索", "").strip()
    
    if not gid_str or not gid_str.isdigit():
        await roblox_group_id_search.finish("请输入有效的群组ID（纯数字），例：/群组ID搜索 123456")
    gid = int(gid_str)
    
    await roblox_group_id_search.send("稍等，正在查询群组信息...")
    total_start = time.time()
    
    try:
        tasks = [get_group_info(gid), get_group_icon(gid), get_group_roles(gid)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        group_info, icon_url, roles = results
        
        if isinstance(group_info, Exception) or not group_info:
            await roblox_group_id_search.finish("未找到该群组ID对应的信息！")
        if isinstance(icon_url, Exception):
            icon_url = ""
        if isinstance(roles, Exception):
            roles = []
        
        name = group_info.get("name", "未知")
        description = group_info.get("description", "").strip() or "无描述"
        member_count = group_info.get("memberCount", 0)
        owner = group_info.get("owner", {})
        owner_name = owner.get("name", "未知") if owner else "未知"
        created = group_info.get("created", "")
        is_public = group_info.get("publicEntryAllowed", False)
        
        try:
            create_date = datetime.fromisoformat(created.replace("Z", "")) if created else None
        except:
            create_date = None
        
        roles_text = ""
        if roles:
            for role in roles[:5]:
                role_name = role.get("name", "未知")
                rank = role.get("rank", 0)
                member_count_role = role.get("memberCount", 0)
                roles_text += f"📌 {role_name}（等级{rank}）：{member_count_role}人\n"
        else:
            roles_text = "暂无职位信息"
        
        output = (
            f"🏠 Roblox 群组ID查询结果\n"
            f"🆔 群组ID：{gid}\n"
            f"📛 群组名：{name}\n"
            f"👥 成员数量：{member_count:,}\n"
            f"👤 群主：{owner_name}\n"
            f"📅 创建时间：{create_date.strftime('%Y-%m-%d') if create_date else '未知'}\n"
            f"🌐 是否公开：{'是' if is_public else '否'}\n\n"
            f"📝 群组描述：\n{description[:200]}{'......' if len(description)>200 else ''}\n\n"
            f"🏆 职位列表(前5个)：\n{roles_text}"
        )
        
        if icon_url:
            msg = MessageSegment.image(icon_url) + output
        else:
            msg = output
        await roblox_group_id_search.finish(msg)

    except ActionFailed:
        await roblox_group_id_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[群组ID搜索错误]", traceback.format_exc())
        await roblox_group_id_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 群组ID搜索耗时: {time.time()-total_start:.2f}s")
