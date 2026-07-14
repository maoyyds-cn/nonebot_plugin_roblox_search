# nonebot_plugin_roblox_search/__init__.py
from nonebot.plugin import PluginMetadata

from .whitelist import load_whitelist, check_whitelist
load_whitelist()

# 导入全部功能模块，原有roblox文件零修改
from . import (
    roblox_menu,
    roblox_query,
    roblox_user_id_search,
    roblox_group_id_search,
    roblox_group_name_search,
    roblox_game_id_search,
    roblox_game_name_search,
    roblox_get_friends,
    roblox_get_followers,
    roblox_get_followings,
)

# 插件元信息（NoneBot2 标准PluginMetadata）
__plugin_meta__ = PluginMetadata(
    name="Roblox查询插件",
    description="Roblox平台综合查询工具，支持用户/游戏/群组、好友粉丝关注列表查询",
    usage="""
发送 /menu 查看全部可用指令
/用户名搜索 [用户名]  根据用户名查询用户
/用户ID搜索 [数字ID]  根据ID查询用户完整资料
/游戏名搜索 [游戏名]  模糊搜索游戏
/游戏ID搜索 [数字ID]  查询游戏详情+公开服务器
/群组名搜索 [群组名]  模糊搜索群组
/群组ID搜索 [数字ID]  查询群组详情与职位
/获取好友列表 [用户ID]  获取前10位好友
/获取粉丝列表 [用户ID]  获取前10位粉丝
/获取关注列表 [用户ID]  获取前10位关注
""".strip(),
    type="application",
    homepage="https://github.com/maoyyds-cn/nonebot-plugin-roblox-search",
    supported_adapters={"~onebot.v11"},
)

# 导出模块，NoneBot自动加载所有命令
__all__ = [
    "roblox_menu",
    "roblox_query",
    "roblox_user_id_search",
    "roblox_group_id_search",
    "roblox_group_name_search",
    "roblox_game_id_search",
    "roblox_game_name_search",
    "roblox_get_friends",
    "roblox_get_followers",
    "roblox_get_followings",
]