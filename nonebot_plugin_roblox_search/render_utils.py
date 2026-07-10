import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "msyh.ttc",
    "simhei.ttf", 
    "simsun.ttc",
    "msyhbd.ttc",
    "arial.ttf",
]

EMOJI_MAP = {
    "📋": "[菜单]",
    "👤": "[用户]",
    "🏷": "[标签]",
    "🏷️": "[标签]",
    "🆔": "[ID]",
    "📅": "[日期]",
    "⏳": "[时长]",
    "👥": "[好友]",
    "🟢": "[在线]",
    "📍": "[位置]",
    "🚫": "[封禁]",
    "📝": "[简介]",
    "🏠": "[群组]",
    "🎭": "[职位]",
    "💎": "[会员]",
    "🌟": "[粉丝]",
    "🔍": "[搜索]",
    "🎮": "[游戏]",
    "👨": "[开发者]",
    "👨‍💻": "[开发者]",
    "📊": "[访问]",
    "🔢": "[人数]",
    "🌐": "[服务器]",
    "✅": "[是]",
    "❌": "[否]",
    "💡": "[提示]",
    "→": "->",
}

import os
def find_font():
    font_paths = [
        "C:\\Windows\\Fonts\\",
        "C:\\Windows\\WinSxS\\",
        os.path.expanduser("~/.fonts/"),
        "/usr/share/fonts/",
        "/Library/Fonts/",
    ]
    for font_name in FONT_CANDIDATES:
        for path in font_paths:
            full_path = os.path.join(path, font_name)
            if os.path.exists(full_path):
                return full_path
    return None

FONT_PATH = find_font()

def replace_emoji(text):
    for emoji, replacement in EMOJI_MAP.items():
        text = text.replace(emoji, replacement)
    return text

def wrap_text(font, text, max_width):
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    
    if current_line:
        lines.append(current_line)
    
    return lines

async def text_to_image(text: str, title: str = "") -> bytes:
    text = replace_emoji(text)
    title = replace_emoji(title)
    
    def _generate():
        lines = text.strip().split("\n")
        font_size = 24
        
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()
        
        line_spacing = 4
        padding = 40
        title_padding = 20
        item_padding = 15
        
        content_max_width = 520
        
        title_height = 0
        if title:
            title_font_size = 32
            try:
                title_font = ImageFont.truetype(FONT_PATH, title_font_size)
            except:
                title_font = font
            title_bbox = title_font.getbbox(title)
            title_height = title_bbox[3] - title_bbox[1] + title_padding * 2
        
        max_width = content_max_width + padding * 2
        total_height = title_height
        
        for line in lines:
            if line.startswith("【"):
                total_height += font_size + item_padding
            else:
                wrapped_lines = wrap_text(font, line, content_max_width)
                total_height += len(wrapped_lines) * (font_size + line_spacing)
        
        total_height += padding * 2
        
        image = Image.new("RGB", (max_width, total_height), (26, 26, 46))
        draw = ImageDraw.Draw(image)
        
        draw.rectangle([10, 10, max_width - 10, total_height - 10], outline=(102, 126, 234), width=2)
        
        y = padding
        
        if title:
            title_font_size = 32
            try:
                title_font = ImageFont.truetype(FONT_PATH, title_font_size)
            except:
                title_font = font
            title_width = title_font.getlength(title)
            draw.text(((max_width - title_width) // 2, y), title, font=title_font, fill=(102, 126, 234))
            y += title_height
            
            draw.line([padding, y, max_width - padding, y], fill=(102, 126, 234), width=2)
            y += 20
        
        for line in lines:
            if line.startswith("【"):
                draw.text((padding, y), line, font=font, fill=(102, 126, 234))
                y += font_size + item_padding
            elif "->" in line:
                parts = line.split("->", 1)
                cmd = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""
                
                cmd_width = font.getlength(cmd)
                
                draw.text((padding, y), cmd, font=font, fill=(102, 126, 234))
                draw.text((padding + cmd_width + 10, y), "-> " + desc, font=font, fill=(200, 200, 200))
                y += font_size + line_spacing
            elif line.startswith("├─") or line.startswith("└─"):
                cleaned = line.replace("├─", "").replace("└─", "").strip()
                if "->" in cleaned:
                    parts = cleaned.split("->", 1)
                    cmd = parts[0].strip()
                    desc = parts[1].strip() if len(parts) > 1 else ""
                    
                    cmd_width = font.getlength(cmd)
                    
                    draw.text((padding, y), cmd, font=font, fill=(102, 126, 234))
                    draw.text((padding + cmd_width + 10, y), "-> " + desc, font=font, fill=(200, 200, 200))
                else:
                    draw.text((padding, y), cleaned, font=font, fill=(255, 255, 255))
                y += font_size + line_spacing
            else:
                wrapped_lines = wrap_text(font, line, content_max_width)
                for wrapped in wrapped_lines:
                    draw.text((padding, y), wrapped, font=font, fill=(255, 255, 255))
                    y += font_size + line_spacing
        
        footer_text = "Roblox查询机器人 · Powered by NoneBot2"
        footer_font_size = 16
        try:
            footer_font = ImageFont.truetype(FONT_PATH, footer_font_size)
        except:
            footer_font = font
        footer_width = footer_font.getlength(footer_text)
        footer_height = font.getbbox(footer_text)[3] - font.getbbox(footer_text)[1]
        draw.text(((max_width - footer_width) // 2, total_height - padding - footer_height), footer_text, font=footer_font, fill=(100, 100, 100))
        
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    
    return await asyncio.to_thread(_generate)


async def rich_text_to_image(text: str, title: str = "", avatar_url: str = "") -> bytes:
    text = replace_emoji(text)
    title = replace_emoji(title)
    
    async def download_avatar(url):
        try:
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
        except:
            pass
        return None
    
    avatar_data = None
    if avatar_url:
        avatar_data = await download_avatar(avatar_url)
    
    def _generate():
        lines = text.strip().split("\n")
        font_size = 24
        
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()
        
        line_spacing = 4
        padding = 40
        title_padding = 20
        section_padding = 20
        avatar_size = 150
        avatar_padding = 20
        
        content_max_width = 520
        
        title_height = 0
        if title:
            title_font_size = 32
            try:
                title_font = ImageFont.truetype(FONT_PATH, title_font_size)
            except:
                title_font = font
            title_bbox = title_font.getbbox(title)
            title_height = title_bbox[3] - title_bbox[1] + title_padding * 2
        
        max_width = content_max_width + padding * 2
        total_height = title_height
        
        if avatar_url:
            total_height += avatar_size + avatar_padding
        
        for line in lines:
            if line.startswith("[简介]") or line.startswith("[群组]") or line.startswith("[职位]") or line.startswith("[服务器]"):
                total_height += font_size + section_padding
            elif line.startswith("【"):
                total_height += font_size + section_padding
            else:
                wrapped_lines = wrap_text(font, line, content_max_width)
                total_height += len(wrapped_lines) * (font_size + line_spacing)
        
        total_height += padding * 2
        
        image = Image.new("RGB", (max_width, total_height), (26, 26, 46))
        draw = ImageDraw.Draw(image)
        
        draw.rectangle([10, 10, max_width - 10, total_height - 10], outline=(102, 126, 234), width=2)
        
        y = padding
        
        if title:
            title_font_size = 32
            try:
                title_font = ImageFont.truetype(FONT_PATH, title_font_size)
            except:
                title_font = font
            title_width = title_font.getlength(title)
            draw.text(((max_width - title_width) // 2, y), title, font=title_font, fill=(102, 126, 234))
            y += title_height
            
            draw.line([padding, y, max_width - padding, y], fill=(102, 126, 234), width=2)
            y += 20
        
        if avatar_url and avatar_data:
            avatar_x = (max_width - avatar_size) // 2
            try:
                avatar_img = Image.open(BytesIO(avatar_data))
                avatar_img = avatar_img.resize((avatar_size, avatar_size))
                
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, avatar_size, avatar_size], fill=255)
                
                circle_avatar = Image.new("RGBA", (avatar_size, avatar_size))
                circle_avatar.paste(avatar_img, (0, 0), mask)
                
                image.paste(circle_avatar, (avatar_x, y), circle_avatar)
                
                draw.ellipse([avatar_x - 3, y - 3, avatar_x + avatar_size + 3, y + avatar_size + 3], outline=(102, 126, 234), width=3)
            except:
                draw.ellipse([avatar_x, y, avatar_x + avatar_size, y + avatar_size], outline=(102, 126, 234), width=3)
                draw.text((avatar_x + 20, y + avatar_size // 2 - font_size // 2), "头像加载失败", font=font, fill=(100, 100, 100))
            y += avatar_size + avatar_padding
        
        for line in lines:
            if line.startswith("[简介]") or line.startswith("[群组]") or line.startswith("[职位]") or line.startswith("[服务器]"):
                draw.text((padding, y), line, font=font, fill=(102, 126, 234))
                y += font_size + section_padding
            elif line.startswith("【"):
                draw.text((padding, y), line, font=font, fill=(102, 126, 234))
                y += font_size + section_padding
            else:
                wrapped_lines = wrap_text(font, line, content_max_width)
                for wrapped in wrapped_lines:
                    draw.text((padding, y), wrapped, font=font, fill=(255, 255, 255))
                    y += font_size + line_spacing
        
        footer_text = "Roblox查询机器人 · Powered by NoneBot2"
        footer_font_size = 16
        try:
            footer_font = ImageFont.truetype(FONT_PATH, footer_font_size)
        except:
            footer_font = font
        footer_width = footer_font.getlength(footer_text)
        footer_height = font.getbbox(footer_text)[3] - font.getbbox(footer_text)[1]
        draw.text(((max_width - footer_width) // 2, total_height - padding - footer_height), footer_text, font=footer_font, fill=(100, 100, 100))
        
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    
    return await asyncio.to_thread(_generate)
