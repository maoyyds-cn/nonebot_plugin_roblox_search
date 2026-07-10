import asyncio
import traceback
import time
from datetime import datetime
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .http_utils import http_get

roblox_group_name_search = on_keyword(["/群组名搜索","群组名搜索"], priority=5, block=True)

async def search_group_by_name(name):
    url = f"https://groups.roblox.com/v1/groups/search?keyword={name}&limit=10"
    return await http_get(url)

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

@roblox_group_name_search.handle()
async def handle_group_name_search(event: Event):
    raw_text = str(event.get_message()).strip()
    group_name = raw_text.replace("/群组名搜索", "").strip()
    
    if not group_name:
        await roblox_group_name_search.finish("请输入群组名，例：/群组名搜索 Roblox")
    await roblox_group_name_search.send("稍等，正在搜索群组...")
    total_start = time.time()
    
    try:
        search_result = await search_group_by_name(group_name)
        groups = search_result.get("data", [])
        if not groups:
            await roblox_group_name_search.finish("未找到匹配的群组，请检查群组名是否正确！")
        
        group = groups[0]
        gid = group.get("id", 0)
        tasks = [get_group_info(gid), get_group_icon(gid)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        group_info, icon_url = results
        
        if isinstance(group_info, Exception) or not group_info:
            group_info = {}
        if isinstance(icon_url, Exception):
            icon_url = ""
        
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
        
        output = (
            f"🏠 Roblox 群组搜索结果\n"
            f"🆔 群组ID：{gid}\n"
            f"📛 群组名：{name}\n"
            f"👥 成员数量：{member_count:,}\n"
            f"👤 群主：{owner_name}\n"
            f"📅 创建时间：{create_date.strftime('%Y-%m-%d') if create_date else '未知'}\n"
            f"🌐 是否公开：{'是' if is_public else '否'}\n\n"
            f"📝 群组描述：\n{description[:300]}{'......' if len(description)>300 else ''}"
        )
        
        if icon_url:
            msg = MessageSegment.image(icon_url) + output
        else:
            msg = output
        await roblox_group_name_search.finish(msg)

    except ActionFailed:
        await roblox_group_name_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[群组名搜索错误]", traceback.format_exc())
        await roblox_group_name_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 群组名搜索耗时: {time.time()-total_start:.2f}s")
