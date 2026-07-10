import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .render_utils import rich_text_to_image
from .http_utils import http_get

roblox_game_id_search = on_keyword(["/游戏ID搜索","游戏ID搜索"], priority=5, block=True)

async def get_game_detail(game_id):
    url = f"https://games.roblox.com/v1/games?universeIds={game_id}"
    data = await http_get(url)
    return data.get("data", [{}])[0]

async def get_game_servers(game_id):
    url = f"https://games.roblox.com/v1/games/{game_id}/servers/Public?limit=3"
    try:
        data = await http_get(url)
        return data.get("data", [])
    except Exception:
        return []

@roblox_game_id_search.handle()
async def handle_game_id_search(event: Event):
    raw_text = str(event.get_message()).strip()
    game_id_str = raw_text.replace("/游戏ID搜索", "").strip()
    
    if not game_id_str or not game_id_str.isdigit():
        await roblox_game_id_search.finish("请输入有效的Roblox游戏ID（纯数字），例：/游戏ID搜索 123456789")
    game_id = int(game_id_str)
    
    await roblox_game_id_search.send("稍等，正在查询游戏信息...")
    total_start = time.time()
    
    try:
        tasks = [get_game_detail(game_id), get_game_servers(game_id)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        game_detail, game_servers = results
        
        if isinstance(game_detail, Exception) or not game_detail:
            await roblox_game_id_search.finish("未找到该游戏ID对应的信息！")
        if isinstance(game_servers, Exception):
            game_servers = []
        
        name = game_detail.get("name", "未知")
        creator = game_detail.get("creator", {}).get("name", "未知")
        play_count = game_detail.get("playing", 0)
        visit_count = game_detail.get("visits", 0)
        max_players = game_detail.get("maxPlayers", 0)
        description = game_detail.get("description", "").strip() or "无简介"
        created = game_detail.get("created", "").split("T")[0] if game_detail.get("created") else "未知"
        
        server_text = ""
        if game_servers:
            for idx, server in enumerate(game_servers):
                server_id = server.get("id", "未知")
                player_count = server.get("playing", 0)
                ping = server.get("ping", 0)
                server_text += f"{idx+1}) 服务器ID：{server_id}\n   在线人数：{player_count}/{max_players} | 延迟：{ping}ms\n"
        else:
            server_text = "暂无公开服务器信息"
        
        output = (
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
        
        try:
            img_bytes = await rich_text_to_image(output, "🎮 Roblox 游戏ID查询结果")
            await roblox_game_id_search.finish(MessageSegment.image(img_bytes))
        except Exception as e:
            print(f"[游戏ID查询渲染错误] {e}")
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
