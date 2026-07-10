import asyncio
import json
import traceback
import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .render_utils import rich_text_to_image
from .http_utils import http_get

roblox_game_name_search = on_keyword(["/游戏名搜索","游戏名搜索"], priority=5, block=True)

async def search_game_by_name(game_name):
    url = f"https://games.roblox.com/v1/games/list?keyword={game_name}&limit=5"
    try:
        data = await http_get(url)
        return data.get("data", [])
    except Exception:
        return []

async def get_game_detail(game_id):
    url = f"https://games.roblox.com/v1/games?universeIds={game_id}"
    try:
        data = await http_get(url)
        return data.get("data", [{}])[0]
    except Exception:
        return {}

@roblox_game_name_search.handle()
async def handle_game_name_search(event: Event):
    raw_text = str(event.get_message()).strip()
    game_name = raw_text.replace("/游戏名搜索", "").strip()
    
    if not game_name:
        await roblox_game_name_search.finish("请输入Roblox游戏名，例：/游戏名搜索 Adopt Me")
    
    await roblox_game_name_search.send("稍等，正在搜索游戏...")
    total_start = time.time()
    
    try:
        game_list = await search_game_by_name(game_name)
        if not game_list:
            await roblox_game_name_search.finish("未找到匹配的游戏！")
        
        tasks = [get_game_detail(g.get("universeId", 0)) for g in game_list]
        game_details = await asyncio.gather(*tasks, return_exceptions=True)
        
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
        
        try:
            img_bytes = await rich_text_to_image(output.strip(), "🎮 Roblox 游戏名搜索")
            await roblox_game_name_search.finish(MessageSegment.image(img_bytes))
        except Exception as e:
            print(f"[游戏名搜索渲染错误] {e}")
            await roblox_game_name_search.finish(output.strip())

    except FinishedException:
        raise
    except ActionFailed:
        await roblox_game_name_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[游戏名搜索错误]", traceback.format_exc())
        await roblox_game_name_search.finish(f"搜索失败：{str(e)}")
    finally:
        print(f"[DEBUG] 游戏名搜索耗时: {time.time()-total_start:.2f}s")
