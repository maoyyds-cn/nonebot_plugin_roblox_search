import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .render_utils import rich_text_to_image
from .http_utils import http_get

roblox_group_name_search = on_keyword(["/群组名搜索","群组名搜索"], priority=5, block=True)

async def search_group_by_name(group_name):
    url = "https://groups.roblox.com/v1/groups/search/lookup?keyword=" + group_name
    try:
        data = await http_get(url)
        return data.get("data", [])[:5]
    except Exception:
        return []

async def get_group_detail(group_id):
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    try:
        return await http_get(url)
    except Exception:
        return {}

@roblox_group_name_search.handle()
async def handle_group_name_search(event: Event):
    raw_text = str(event.get_message()).strip()
    group_name = raw_text.replace("/群组名搜索", "").strip()
    
    if not group_name:
        await roblox_group_name_search.finish("请输入Roblox群组名，例：/群组名搜索 Roblox")
    
    await roblox_group_name_search.send("稍等，正在搜索群组...")
    total_start = time.time()
    
    try:
        group_list = await search_group_by_name(group_name)
        if not group_list:
            await roblox_group_name_search.finish("未找到匹配的群组！")
        
        tasks = [get_group_detail(g.get("id", 0)) for g in group_list]
        group_details = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = f"🔍 群组名搜索结果（共{len(group_list)}个）：\n\n"
        for idx, (group, detail) in enumerate(zip(group_list, group_details)):
            group_id = group.get("id", 0)
            name = group.get("name", "未知")
            if isinstance(detail, Exception):
                detail = {}
            
            member_count = detail.get("memberCount", 0)
            owner_name = detail.get("owner", {}).get("username", "未知")
            owner_id = detail.get("owner", {}).get("userId", 0)
            description = detail.get("description", "").strip()[:100] or "无简介"
            
            output += (
                f"【{idx+1}】\n"
                f"群组名：{name}\n"
                f"群组ID：{group_id}\n"
                f"成员数：{member_count}\n"
                f"群主：{owner_name}（ID：{owner_id}）\n"
                f"简介：{description}\n\n"
            )
        
        try:
            img_bytes = await rich_text_to_image(output.strip(), "🔍 Roblox 群组名搜索")
            await roblox_group_name_search.finish(MessageSegment.image(img_bytes))
        except Exception as e:
            print(f"[群组名搜索渲染错误] {e}")
            await roblox_group_name_search.finish(output.strip())

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_group_name_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[群组名搜索错误]", traceback.format_exc())
        await roblox_group_name_search.finish(f"搜索失败：{str(e)}")
    finally:
        print(f"[DEBUG] 群组名搜索耗时: {time.time()-total_start:.2f}s")
