import os
import logging

logger = logging.getLogger(__name__)

SEARCH_WHITE_LIST = []
PLUGIN_ENABLED = True

def load_whitelist():
    global SEARCH_WHITE_LIST, PLUGIN_ENABLED
    
    env_files = ['.env', '.env.dev', '.env.prod']
    found = False
    
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('SEARCHWHITE='):
                        value = line.split('=', 1)[1]
                        try:
                            SEARCH_WHITE_LIST = eval(value)
                            if isinstance(SEARCH_WHITE_LIST, list):
                                SEARCH_WHITE_LIST = [str(item) for item in SEARCH_WHITE_LIST]
                                found = True
                                logger.info(f"[nonebot-plugin-roblox-search] 白名单加载成功: {SEARCH_WHITE_LIST}")
                            break
                        except Exception as e:
                            logger.error(f"[nonebot-plugin-roblox-search] 白名单配置解析错误: {e}")
                            break
    
    if not found:
        PLUGIN_ENABLED = False
        logger.error("[nonebot-plugin-roblox-search] 请在.env.dev或者是.env或者是.env.prod中加上SEARCHWHITE=[\"群号\"]这个配置项，否则无法使用nonebot-plugin-roblox-search插件！")

def check_whitelist(group_id: str) -> bool:
    if not PLUGIN_ENABLED:
        return False
    if not SEARCH_WHITE_LIST:
        return False
    return group_id in SEARCH_WHITE_LIST
