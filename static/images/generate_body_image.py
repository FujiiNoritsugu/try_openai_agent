"""
クリック可能な領域を持つシンプルな人体画像を生成する。
"""
from PIL import Image, ImageDraw, ImageFont
import os

width, height = 400, 600
image = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(image)

body_parts = {
    "頭": [(175, 50), (225, 100)],  # 頭
    "顔": [(175, 100), (225, 150)],  # 顔
    "首": [(190, 150), (210, 170)],  # 首
    "肩": [(150, 170), (250, 190)],  # 肩
    "腕": [(130, 190), (150, 270), (250, 190), (270, 270)],  # 腕
    "手": [(120, 270), (140, 300), (260, 270), (280, 300)],  # 手
    "胸": [(170, 190), (230, 240)],  # 胸
    "腹": [(170, 240), (230, 300)],  # 腹
    "腰": [(170, 300), (230, 330)],  # 腰
    "臀部": [(170, 330), (230, 370)],  # 臀部
    "脚": [(160, 370), (190, 500), (210, 370), (240, 500)],  # 脚
    "足": [(150, 500), (190, 530), (210, 500), (250, 530)]  # 足
}

draw.ellipse([(175, 50), (225, 100)], outline='black', width=2)
draw.rectangle([(175, 100), (225, 150)], outline='black', width=2)
draw.rectangle([(190, 150), (210, 170)], outline='black', width=2)
draw.rectangle([(170, 170), (230, 330)], outline='black', width=2)
draw.line([(150, 170), (250, 170)], fill='black', width=2)
draw.line([(150, 170), (130, 270)], fill='black', width=2)
draw.line([(250, 170), (270, 270)], fill='black', width=2)
draw.ellipse([(120, 270), (140, 300)], outline='black', width=2)
draw.ellipse([(260, 270), (280, 300)], outline='black', width=2)
draw.rectangle([(170, 330), (230, 370)], outline='black', width=2)
draw.line([(170, 370), (160, 500)], fill='black', width=2)
draw.line([(230, 370), (240, 500)], fill='black', width=2)
draw.ellipse([(150, 500), (190, 530)], outline='black', width=2)
draw.ellipse([(210, 500), (250, 530)], outline='black', width=2)

for part, coords in body_parts.items():
    if part in ["腕", "手", "脚", "足"]:
        x = (coords[0][0] + coords[1][0]) // 2
        y = (coords[0][1] + coords[1][1]) // 2
    else:
        x = (coords[0][0] + coords[1][0]) // 2
        y = (coords[0][1] + coords[1][1]) // 2
    
    draw.text((x, y), part, fill='black')

os.makedirs('static/images', exist_ok=True)
image.save('static/images/human_body.png')

with open('static/images/body_map.txt', 'w', encoding='utf-8') as f:
    for part, coords in body_parts.items():
        if part in ["腕", "手", "脚", "足"]:
            f.write(f"{part},{coords[0][0]},{coords[0][1]},{coords[1][0]},{coords[1][1]}\n")
        else:
            f.write(f"{part},{coords[0][0]},{coords[0][1]},{coords[1][0]},{coords[1][1]}\n")

print("人体画像とマップファイルが正常に作成されました。")
