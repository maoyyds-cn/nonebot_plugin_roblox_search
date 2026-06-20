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

# 触发关键词：/游戏名搜索
roblox_game_name_search = on_keyword(["/游戏名搜索","游戏名搜索"], priority=5, block=True)

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

async def search_game_by_name(game_name):
    """根据游戏名搜索"""
    url = f"https://games.roblox.com/v1/games/list?keyword={game_name}&limit=5"
    try:
        data = await curl_request("GET", url)
        return data.get("data", [])
    except Exception:
        return []

async def get_game_detail(game_id):
    """获取游戏详情"""
    url = f"https://games.roblox.com/v1/games?universeIds={game_id}"
    try:
        data = await curl_request("GET", url)
        return data.get("data", [{}])[0]
    except Exception:
        return {}

@roblox_game_name_search.handle()
async def handle_game_name_search(event: Event):
    # 提取游戏名
    raw_text = str(event.get_message()).strip()
    game_name = raw_text.replace("/游戏名搜索", "").strip()
    
    if not game_name:
        await roblox_game_name_search.finish("请输入Roblox游戏名，例：/游戏名搜索 Adopt Me")
    
    await roblox_game_name_search.send("稍等，正在搜索游戏...")
    total_start = time.time()
    
    try:
        # 搜索游戏
        game_list = await search_game_by_name(game_name)
        if not game_list:
            await roblox_game_name_search.finish("未找到匹配的游戏！")
        
        # 批量获取游戏详情
        tasks = [get_game_detail(g.get("universeId", 0)) for g in game_list]
        game_details = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 组装结果
        output = f"🎮 游戏名搜索结果（共{len(game_list)}个）：\n\n"
        for idx, (game, detail) in enumerate(zip(game_list, game_details)):
            game_id = game.get("universeId", 0)
            name = game.get("name", "未知")
            creator = game.get("creator", {}).get("name", "未知")
            
            if isinstance(detail, Exception):
                detail = {}
            play_count = detail.get("playing", 0)
            visit_count = detail.get("visits", 0)
            description = detail.get("description", "").strip()[:100] or "无简介"
            
            output += (
                f"【{idx+1}】\n"
                f"游戏名：{name}\n"
                f"游戏ID：{game_id}\n"
                f"开发者：{creator}\n"
                f"当前在线：{play_count}\n"
                f"总访问量：{visit_count}\n"
                f"简介：{description}\n\n"
            )
        
        await roblox_game_name_search.finish(output.strip())

    except ActionFailed:
        raise
    except Exception as e:
        print("[游戏名搜索错误]", traceback.format_exc())
        await roblox_game_name_search.finish(f"搜索失败：{str(e)}")
    finally:
        print(f"[DEBUG] 游戏名搜索耗时: {time.time()-total_start:.2f}s")