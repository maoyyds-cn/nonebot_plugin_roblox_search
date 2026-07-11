import time
from nonebot import on_keyword
from nonebot.adapters.onebot.v11 import Event, MessageSegment
from nonebot.exception import FinishedException
from .render_utils import menu_to_image

roblox_menu = on_keyword(["菜单", "帮助", "menu", "/菜单", "/帮助", "/menu"], priority=5, block=True)

@roblox_menu.handle()
async def handle_menu(event: Event):
    start_time = time.time()
    msg = str(event.get_message()).strip()
    valid_commands = ["菜单", "帮助", "menu", "/菜单", "/帮助", "/menu"]
    
    if msg not in valid_commands:
        return
    
    try:
        img_bytes = await menu_to_image()
        await roblox_menu.finish(MessageSegment.image(img_bytes))
    except FinishedException:
        raise
    except Exception as e:
        print(f"[菜单生成错误]: {e}")
        await roblox_menu.finish("菜单生成失败，请稍后重试")
    finally:
        print(f"[DEBUG] 菜单生成耗时: {time.time()-start_time:.2f}s")
