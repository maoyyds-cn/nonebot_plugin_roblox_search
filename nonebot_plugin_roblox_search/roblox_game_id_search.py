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

# 触发关键词：/游戏ID搜索
roblox_game_id_search = on_keyword(["/游戏ID搜索","游戏ID搜索"], priority=5, block=True)

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

async def get_game_detail(game_id):
    """根据游戏ID获取详情"""
    url = f"https://games.roblox.com/v1/games?universeIds={game_id}"
    data = await curl_request("GET", url)
    return data.get("data", [{}])[0]

async def get_game_servers(game_id):
    """获取游戏服务器列表（前3个）"""
    url = f"https://games.roblox.com/v1/games/{game_id}/servers/Public?limit=3"
    try:
        data = await curl_request("GET", url)
        return data.get("data", [])
    except Exception:
        return []

@roblox_game_id_search.handle()
async def handle_game_id_search(event: Event):
    # 提取游戏ID
    raw_text = str(event.get_message()).strip()
    game_id_str = raw_text.replace("/游戏ID搜索", "").strip()
    
    if not game_id_str or not game_id_str.isdigit():
        await roblox_game_id_search.finish("请输入有效的Roblox游戏ID（纯数字），例：/游戏ID搜索 123456789")
    game_id = int(game_id_str)
    
    await roblox_game_id_search.send("稍等，正在查询游戏信息...")
    total_start = time.time()
    
    try:
        # 并发请求数据
        tasks = [get_game_detail(game_id), get_game_servers(game_id)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        game_detail, game_servers = results
        
        # 异常兜底
        if isinstance(game_detail, Exception) or not game_detail:
            await roblox_game_id_search.finish("未找到该游戏ID对应的信息！")
        if isinstance(game_servers, Exception):
            game_servers = []
        
        # 解析信息
        name = game_detail.get("name", "未知")
        creator = game_detail.get("creator", {}).get("name", "未知")
        play_count = game_detail.get("playing", 0)
        visit_count = game_detail.get("visits", 0)
        max_players = game_detail.get("maxPlayers", 0)
        description = game_detail.get("description", "").strip() or "无简介"
        created = game_detail.get("created", "").split("T")[0] if game_detail.get("created") else "未知"
        
        # 服务器列表
        server_text = ""
        if game_servers:
            for idx, server in enumerate(game_servers):
                server_id = server.get("id", "未知")
                player_count = server.get("playing", 0)
                ping = server.get("ping", 0)
                server_text += f"{idx+1}) 服务器ID：{server_id}\n   在线人数：{player_count}/{max_players} | 延迟：{ping}ms\n"
        else:
            server_text = "暂无公开服务器信息"
        
        # 组装输出
        output = (
            f"🎮 Roblox 游戏ID查询结果\n"
            f"🆔 游戏ID：{game_id}\n"
            f"📛 游戏名：{name}\n"
            f"📅 创建时间：{created}\n"
            f"👨‍💻 开发者：{creator}\n"
            f"👥 当前在线：{play_count}\n"
            f"📊 总访问量：{visit_count}\n"
            f"🔢 最大人数：{max_players}\n\n"
            f"📝 简介：\n{description[:300]}{'......' if len(description)>300 else ''}\n\n"
            f"🌐 公开服务器（前3个）：\n{server_text}"
        )
        
        await roblox_game_id_search.finish(output)

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_game_id_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[游戏ID搜索错误]", traceback.format_exc())
        await roblox_game_id_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 游戏ID搜索耗时: {time.time()-total_start:.2f}s")