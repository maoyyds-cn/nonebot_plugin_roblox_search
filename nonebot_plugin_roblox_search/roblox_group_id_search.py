import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException

HEADERS = [
    "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]
TIMEOUT = 30

# 触发关键词：/群组ID搜索
roblox_group_id_search = on_keyword(["/群组ID搜索","群组ID搜索"], priority=5, block=True)

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

async def get_group_detail(group_id):
    """根据群组ID获取详情"""
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    return await curl_request("GET", url)

async def get_group_roles(group_id):
    """获取群组职位列表"""
    url = f"https://groups.roblox.com/v1/groups/{group_id}/roles"
    try:
        data = await curl_request("GET", url)
        return data.get("roles", [])[:5]  # 前5个职位
    except Exception:
        return []

@roblox_group_id_search.handle()
async def handle_group_id_search(event: Event):
    # 提取群组ID
    raw_text = str(event.get_message()).strip()
    group_id_str = raw_text.replace("/群组ID搜索", "").strip()
    
    if not group_id_str or not group_id_str.isdigit():
        await roblox_group_id_search.finish("请输入有效的Roblox群组ID（纯数字），例：/群组ID搜索 123456789")
    group_id = int(group_id_str)
    
    await roblox_group_id_search.send("稍等，正在查询群组信息...")
    total_start = time.time()
    
    try:
        # 并发请求数据
        tasks = [get_group_detail(group_id), get_group_roles(group_id)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        group_detail, group_roles = results
        
        # 异常兜底
        if isinstance(group_detail, Exception) or not group_detail:
            await roblox_group_id_search.finish("未找到该群组ID对应的信息！")
        if isinstance(group_roles, Exception):
            group_roles = []
        
        # 解析信息
        name = group_detail.get("name", "未知")
        description = group_detail.get("description", "").strip() or "无简介"
        member_count = group_detail.get("memberCount", 0)
        owner_name = group_detail.get("owner", {}).get("username", "未知")
        owner_id = group_detail.get("owner", {}).get("userId", 0)
        created = group_detail.get("created", "").split("T")[0] if group_detail.get("created") else "未知"
        
        # 职位列表
        role_text = ""
        if group_roles:
            for idx, role in enumerate(group_roles):
                role_name = role.get("name", "未知")
                role_rank = role.get("rank", 0)
                role_count = role.get("memberCount", 0)
                role_text += f"{idx+1}) {role_name}（等级{role_rank}，成员{role_count}人）\n"
        else:
            role_text = "暂无职位信息"
        
        # 组装输出
        output = (
            f"🏠 Roblox 群组ID查询结果\n"
            f"🆔 群组ID：{group_id}\n"
            f"📛 群组名：{name}\n"
            f"📅 创建时间：{created}\n"
            f"👥 成员总数：{member_count}\n"
            f"👑 群主：{owner_name}（ID：{owner_id}）\n\n"
            f"📝 简介：\n{description[:300]}{'......' if len(description)>300 else ''}\n\n"
            f"🎭 职位列表（前5个）：\n{role_text}"
        )
        
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