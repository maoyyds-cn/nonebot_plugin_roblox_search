import asyncio
import traceback
import time
from datetime import datetime
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .http_utils import http_get
from .render_utils import text_to_image

roblox_game_name_search = on_keyword(["/游戏名搜索","游戏名搜索"], priority=5, block=True)

async def search_game_by_name(name):
    url = f"https://games.roblox.com/v1/games/list?accessFilter=2&keyword={name}&limit=10&sortOrder=Relevance"
    return await http_get(url)

async def get_game_info(place_id):
    url = f"https://games.roblox.com/v1/games?placeIds={place_id}"
    return await http_get(url)

async def get_game_icon(game_id):
    url = f"https://thumbnails.roblox.com/v1/games/icons?gameIds={game_id}&size=512x512&format=Png&isCircular=false"
    try:
        data = await http_get(url)
        return data.get("data", [{}])[0].get("imageUrl", "")
    except Exception:
        return ""

@roblox_game_name_search.handle()
async def handle_game_name_search(event: Event):
    raw_text = str(event.get_message()).strip()
    game_name = raw_text.replace("/游戏名搜索", "").strip()
    
    if not game_name:
        await roblox_game_name_search.finish("请输入游戏名，例：/游戏名搜索 Adopt Me")
    await roblox_game_name_search.send("稍等，正在搜索游戏...")
    total_start = time.time()
    
    try:
        search_result = await search_game_by_name(game_name)
        games = search_result.get("data", [])
        if not games:
            await roblox_game_name_search.finish("未找到匹配的游戏，请检查游戏名是否正确！")
        
        game = games[0]
        place_id = game.get("placeId", 0)
        game_id = game.get("id", 0)
        tasks = [get_game_info(place_id), get_game_icon(game_id)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        game_info, icon_url = results
        
        if isinstance(game_info, Exception) or not game_info:
            game_info = {}
        if isinstance(icon_url, Exception):
            icon_url = ""
        
        games_data = game_info.get("data", [])
        if not games_data:
            game_detail = {}
        else:
            game_detail = games_data[0]
        
        name = game_detail.get("name", game.get("name", "未知"))
        description = game_detail.get("description", "").strip() or "无描述"
        creator = game_detail.get("creator", {})
        creator_name = creator.get("name", "未知") if creator else game.get("creatorName", "未知")
        playing = game_detail.get("playing", 0)
        visits = game_detail.get("visits", 0)
        favorites = game_detail.get("favorites", 0)
        created = game_detail.get("created", "")
        updated = game_detail.get("updated", "")
        
        try:
            create_date = datetime.fromisoformat(created.replace("Z", "")) if created else None
            update_date = datetime.fromisoformat(updated.replace("Z", "")) if updated else None
        except:
            create_date = None
            update_date = None
        
        output = (
            f"🆔 游戏ID：{game_id}\n"
            f"📍 地点ID：{place_id}\n"
            f"📛 游戏名：{name}\n"
            f"👤 开发者：{creator_name}\n"
            f"👥 当前游玩：{playing:,}\n"
            f"👁️ 总访问量：{visits:,}\n"
            f"❤️ 收藏数：{favorites:,}\n"
            f"📅 创建时间：{create_date.strftime('%Y-%m-%d') if create_date else '未知'}\n"
            f"🔄 更新时间：{update_date.strftime('%Y-%m-%d') if update_date else '未知'}\n\n"
            f"📝 游戏描述：\n{description[:300]}{'......' if len(description)>300 else ''}"
        )
        
        img_bytes = await text_to_image(output, title="🎮 Roblox 游戏搜索结果", avatar_url=icon_url)
        await roblox_game_name_search.finish(MessageSegment.image(img_bytes))

    except ActionFailed:
        await roblox_game_name_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except Exception as e:
        print("[游戏名搜索错误]", traceback.format_exc())
        await roblox_game_name_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 游戏名搜索耗时: {time.time()-total_start:.2f}s")
