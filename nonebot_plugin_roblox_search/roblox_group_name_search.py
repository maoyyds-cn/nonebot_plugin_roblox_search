import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed

HEADERS = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
TIMEOUT = 30

# 触发关键词：/群组名搜索
roblox_group_name_search = on_keyword(["/群组名搜索","群组名搜索"], priority=5, block=True)

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

async def search_group_by_name(group_name):
    """根据群组名搜索（Roblox无直接搜索API，用模糊匹配+列表接口兜底）"""
    # 注：Roblox无公开的"群组名搜索"API，此处用热门群组列表+模糊匹配模拟（可根据实际API调整）
    # 若有正式搜索API，替换此函数即可
    url = "https://groups.roblox.com/v1/groups/search/lookup?keyword=" + group_name
    try:
        data = await curl_request("GET", url)
        return data.get("data", [])[:5]  # 返回前5个匹配结果
    except Exception:
        # 兜底：无搜索结果返回空
        return []

async def get_group_detail(group_id):
    """获取群组详情"""
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    try:
        return await curl_request("GET", url)
    except Exception:
        return {}

@roblox_group_name_search.handle()
async def handle_group_name_search(event: Event):
    # 提取群组名
    raw_text = str(event.get_message()).strip()
    group_name = raw_text.replace("/群组名搜索", "").strip()
    
    if not group_name:
        await roblox_group_name_search.finish("请输入Roblox群组名，例：/群组名搜索 Roblox")
    
    await roblox_group_name_search.send("稍等，正在搜索群组...")
    total_start = time.time()
    
    try:
        # 搜索群组
        group_list = await search_group_by_name(group_name)
        if not group_list:
            await roblox_group_name_search.finish("未找到匹配的群组！")
        
        # 批量获取群组详情
        tasks = [get_group_detail(g.get("id", 0)) for g in group_list]
        group_details = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 组装结果
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
        
        await roblox_group_name_search.finish(output.strip())

    except ActionFailed:
        raise
    except Exception as e:
        print("[群组名搜索错误]", traceback.format_exc())
        await roblox_group_name_search.finish(f"搜索失败：{str(e)}")
    finally:
        print(f"[DEBUG] 群组名搜索耗时: {time.time()-total_start:.2f}s")