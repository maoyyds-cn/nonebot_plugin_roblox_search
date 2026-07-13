# nonebot-plugin-roblox-search

NoneBot2 Roblox 全功能查询插件，基于系统curl请求，无需aiohttp，低环境依赖

## 功能清单

- `/菜单`：查看全部指令（图片形式）
- `/用户名搜索 [用户名]`：通过用户名查询用户完整资料、头像、虚拟形象
- `/用户ID搜索 [数字ID]`：直接UID查询用户，包含头像和虚拟形象
- `/群组名搜索 [群组名]`：模糊搜索群组并展示详情
- `/群组ID搜索 [数字ID]`：群组ID精准查询、职位列表
- `/游戏名搜索 [游戏名]`：搜索游戏、在线人数、访问量
- `/游戏ID搜索 [数字ID]`：游戏详情+公开服务器列表
- `/获取好友列表 [用户ID]`：读取用户前10位好友
- `/获取粉丝列表 [用户ID]`：读取前10位粉丝
- `/获取关注列表 [用户ID]`：读取前10位关注

## 特性

1. 使用系统curl异步调用，规避服务器Python环境冲突
2. 多层异常捕获，单个接口失效不崩溃整条查询
3. 自动截断超长文本，适配QQ消息长度限制
4. 自带查询耗时日志，方便排错
5. 兼容Linux/Windows/Mac（需系统内置curl）
6. 自动检测系统中文字体，无需手动安装
7. 菜单以精美图片形式展示
8. 用户查询自动获取头像和虚拟形象

## 前置依赖

1. Python >=3.10
2. NoneBot2 + OneBot V11适配器
3. 系统安装curl（Linux默认自带，Windows需安装Git Bash或单独curl）

## 安装方式

### 使用nb-cli安装（推荐）

```bash
nb plugin install nonebot-plugin-roblox-search
```

### 使用pip安装

```bash
pip install nonebot-plugin-roblox-search
```

## 使用说明

安装后，发送 `/菜单` 即可查看所有可用指令。

## 输出效果

用户查询会同时显示：

- 用户头像（Headshot）
- 用户虚拟形象（Avatar）
- 用户详细信息（文字）

