import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .render_utils import rich_text_to_image
from .http_utils import http_get

roblox_group_id_search = on_keyword(["/群组ID搜索","群组ID搜索"], priority=5, block=True)

async def get_group_detail(group_id):
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    return await http_get(url)

async def get_group_roles(group_id):
    url = f"https://groups.roblox.com/v1/groups/{group_id}/roles"
    try:
        data = await http_get(url)
        return data.get("roles", [])[:5]
    except Exception:
        return []

@roblox_group_id_search.handle()
async def handle_group_id_search(event: Event):
    raw_text = str(event.get_message()).strip()
    group_id_str = raw_text.replace("/群组ID搜索", "").strip()
    
    if not group_id_str or not group_id_str.isdigit():
        await roblox_group_id_search.finish("请输入有效的Roblox群组ID（纯数字），例：/群组ID搜索 123456789")
    group_id = int(group_id_str)
    
    await roblox_group_id_search.send("稍等，正在查询群组信息...")
    total_start = time.time()
    
    try:
        tasks = [get_group_detail(group_id), get_group_roles(group_id)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        group_detail, group_roles = results
        
        if isinstance(group_detail, Exception) or not group_detail:
            await roblox_group_id_search.finish("未找到该群组ID对应的信息！")
        if isinstance(group_roles, Exception):
            group_roles = []
        
        name = group_detail.get("name", "未知")
        description = group_detail.get("description", "").strip() or "无简介"
        member_count = group_detail.get("memberCount", 0)
        owner_name = group_detail.get("owner", {}).get("username", "未知")
        owner_id = group_detail.get("owner", {}).get("userId", 0)
        created = group_detail.get("created", "").split("T")[0] if group_detail.get("created") else "未知"
        
        role_text = ""
        if group_roles:
            for idx, role in enumerate(group_roles):
                role_name = role.get("name", "未知")
                role_rank = role.get("rank", 0)
                role_count = role.get("memberCount", 0)
                role_text += f"{idx+1}) {role_name}（等级{role_rank}，成员{role_count}人）\n"
        else:
            role_text = "暂无职位信息"
        
        output = (
            f"🆔 群组ID：{group_id}\n"
            f"📛 群组名：{name}\n"
            f"📅 创建时间：{created}\n"
            f"👥 成员总数：{member_count}\n"
            f"👑 群主：{owner_name}（ID：{owner_id}）\n\n"
            f"📝 简介：\n{description[:300]}{'......' if len(description)>300 else ''}\n\n"
            f"🎭 职位列表（前5个）：\n{role_text}"
        )
        
        try:
            img_bytes = await rich_text_to_image(output, "🏠 Roblox 群组ID查询结果")
            await roblox_group_id_search.finish(MessageSegment.image(img_bytes))
        except Exception as e:
            print(f"[群组ID查询渲染错误] {e}")
            await roblox_group_id_search.finish(output)

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_group_id_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[群组ID搜索错误]", traceback.format_exc())
        await roblox_group_id_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 群组ID搜索耗时: {time.time()-total_start:.2f}s")
