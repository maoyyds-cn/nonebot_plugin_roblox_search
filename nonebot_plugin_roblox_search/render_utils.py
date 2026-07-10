import asyncio
import io
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def get_font(size=14):
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def split_text(text, font, max_width):
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph:
            lines.append('')
            continue
        current_line = ''
        for char in paragraph:
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
    return lines

async def text_to_image(text: str, title: str = "", avatar_url: str = "") -> bytes:
    font = get_font(16)
    title_font = get_font(22)
    small_font = get_font(12)
    
    content_width = 700
    padding = 40
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1] + 6
    
    lines = split_text(text, font, content_width - padding * 2)
    
    title_height = 0
    if title:
        title_lines = split_text(title, title_font, content_width - padding * 2)
        title_height = len(title_lines) * (line_height + 4) + 20
    
    footer_height = 40
    image_height = title_height + len(lines) * line_height + padding * 2 + footer_height
    
    if avatar_url:
        image_height += 140
    
    img = Image.new('RGB', (content_width, image_height), color=(18, 22, 35))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(5, 5), (content_width - 5, image_height - 5)], outline=(60, 120, 255), width=2)
    
    y = padding
    if title:
        for title_line in title_lines:
            bbox = title_font.getbbox(title_line)
            text_width = bbox[2] - bbox[0]
            x = (content_width - text_width) // 2
            draw.text((x, y), title_line, font=title_font, fill=(60, 180, 255))
            y += line_height + 4
        y += 10
        draw.line([(padding, y), (content_width - padding, y)], fill=(40, 80, 150), width=2)
        y += 15
    
    if avatar_url:
        try:
            import requests
            response = requests.get(avatar_url, timeout=10)
            if response.status_code == 200:
                avatar_img = Image.open(io.BytesIO(response.content))
                avatar_size = 100
                avatar_img = avatar_img.resize((avatar_size, avatar_size))
                avatar_x = (content_width - avatar_size) // 2
                draw.ellipse([(avatar_x - 5, y - 5), (avatar_x + avatar_size + 5, y + avatar_size + 5)], outline=(60, 120, 255), width=3)
                img.paste(avatar_img, (avatar_x, y))
                y += avatar_size + 20
        except:
            pass
    
    for line in lines:
        draw.text((padding, y), line, font=font, fill=(200, 210, 230))
        y += line_height
    
    footer_text = "Roblox查询机器人 · Powered by NoneBot2"
    bbox = small_font.getbbox(footer_text)
    footer_width = bbox[2] - bbox[0]
    footer_x = (content_width - footer_width) // 2
    draw.text((footer_x, image_height - 30), footer_text, font=small_font, fill=(80, 100, 130))
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()
