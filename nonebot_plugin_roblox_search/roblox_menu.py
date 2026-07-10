from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, Message, MessageSegment
from nonebot.exception import ActionFailed
from .render_utils import text_to_image

roblox_menu = on_keyword(["/menu","menu"], priority=5, block=True)

@roblox_menu.handle()
async def handle_menu(event: Event):
    menu_text = """
📋 Roblox 查询机器人指令菜单(指令前加斜杠或者空格都行)
├─ /用户名搜索 [用户名] → 根据用户名查询用户信息
├─ /群组名搜索 [群组名] → 根据群组名搜索群组
├─ /游戏名搜索 [游戏名] → 根据游戏名搜索游戏
├─ /用户ID搜索 [用户ID] → 根据ID查询用户信息
├─ /群组ID搜索 [群组ID] → 根据ID查询群组信息
├─ /游戏ID搜索 [游戏ID] → 根据ID查询游戏信息
├─ /获取好友列表 [用户ID] → 获取用户好友列表（前10个）
├─ /获取粉丝列表 [用户ID] → 获取用户粉丝列表（前10个）
└─ /获取关注列表 [用户ID] → 获取用户关注列表（前10个）

💡 示例：/用户名搜索 maochina_4
    """.strip()
    try:
        img_bytes = await text_to_image(menu_text, "📋 Roblox 查询指令菜单")
        await roblox_menu.finish(MessageSegment.image(img_bytes))
    except Exception as e:
        print(f"[菜单渲染错误] {e}")
        await roblox_menu.finish(menu_text)