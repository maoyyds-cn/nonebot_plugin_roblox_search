import asyncio
import traceback
import time
from datetime import datetime
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, MessageSegment
from nonebot.exception import ActionFailed, FinishedException
from .http_utils import http_get
from .whitelist import check_whitelist

roblox_game_id_search = on_keyword(["/游戏ID搜索","游戏ID搜索"], priority=5, block=True)

async def get_game_info(game_id):
    url = f"https://games.rotunnel.com/v1/games?placeIds={game_id}"
    return await http_get(url)

async def get_game_icon(game_id):
    url = f"https://thumbnails.rotunnel.com/v1/games/icons?gameIds={game_id}&size=512x512&format=Png&isCircular=false"
    try:
        data = await http_get(url)
        return data.get("data", [{}])[0].get("imageUrl", "")
    except Exception:
        return ""

async def get_game_servers(game_id):
    url = f"https://games.rotunnel.com/v1/games/{game_id}/servers/Public?limit=5"
    try:
        data = await http_get(url)
        return data.get("data", [])
    except Exception:
        return []

@roblox_game_id_search.handle()
async def handle_game_id_search(event: Event):
    raw_text = str(event.get_message()).strip()
    game_id_str = raw_text.replace("游戏ID搜索", "").replace("/游戏ID搜索", "").strip()
    
    if not game_id_str or not game_id_str.isdigit():
        await roblox_game_id_search.finish("请输入有效的游戏ID（纯数字），例：/游戏ID搜索 123456789")
    game_id = int(game_id_str)
    
    group_id = str(event.group_id) if hasattr(event, 'group_id') else "private"
    if group_id != "private" and not check_whitelist(group_id):
        await roblox_game_id_search.finish("此群未获得账号所有者的允许，未开放此群白名单，暂时不开使用，请联系账号所有者")
    
    await roblox_game_id_search.send("稍等，正在查询游戏信息...")
    total_start = time.time()
    
    try:
        tasks = [get_game_info(game_id), get_game_icon(game_id), get_game_servers(game_id)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        game_info, icon_url, servers = results
        
        if isinstance(game_info, Exception) or not game_info:
            await roblox_game_id_search.finish("未找到该游戏ID对应的信息！")
        if isinstance(icon_url, Exception):
            icon_url = ""
        if isinstance(servers, Exception):
            servers = []
        
        games_data = game_info.get("data", [])
        if not games_data:
            await roblox_game_id_search.finish("未找到该游戏ID对应的信息！")
        
        game_detail = games_data[0]
        name = game_detail.get("name", "未知")
        description = game_detail.get("description", "").strip() or "无描述"
        creator = game_detail.get("creator", {})
        creator_name = creator.get("name", "未知") if creator else "未知"
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
        
        servers_text = ""
        if servers:
            for server in servers[:3]:
                players = server.get("playing", 0)
                max_players = server.get("maxPlayers", 0)
                ping = server.get("ping", 0)
                servers_text += f"📍 服务器：{players}/{max_players}人 | 延迟：{ping}ms\n"
        else:
            servers_text = "暂无公开服务器信息"
        
        output = f"🎮 Roblox 游戏ID查询结果\n\n"
        output += f"🆔 游戏ID：{game_id}\n"
        output += f"📛 游戏名：{name}\n"
        output += f"👤 开发者：{creator_name}\n"
        output += f"👥 当前游玩：{playing:,}\n"
        output += f"👁️ 总访问量：{visits:,}\n"
        output += f"❤️ 收藏数：{favorites:,}\n"
        output += f"📅 创建时间：{create_date.strftime('%Y-%m-%d') if create_date else '未知'}\n"
        output += f"🔄 更新时间：{update_date.strftime('%Y-%m-%d') if update_date else '未知'}\n\n"
        output += f"📝 游戏描述：\n{description[:200]}{'......' if len(description)>200 else ''}\n\n"
        output += f"🌐 公开服务器(前3个)：\n{servers_text}"
        
        messages = []
        
        if icon_url:
            try:
                import requests
                response = requests.get(icon_url, timeout=5)
                if response.status_code == 200:
                    messages.append(MessageSegment.image(response.content))
            except:
                pass
        
        messages.append(output)
        
        await roblox_game_id_search.finish(messages)

    except ActionFailed:
        await roblox_game_id_search.finish("消息发送失败，可能是bot被禁言或对方已离线")
    except FinishedException:
        raise
    except Exception as e:
        print("[游戏ID搜索错误]", traceback.format_exc())
        await roblox_game_id_search.finish(f"查询失败：{str(e)}")
    finally:
        print(f"[DEBUG] 游戏ID搜索耗时: {time.time()-total_start:.2f}s")
