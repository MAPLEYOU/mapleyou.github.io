"""v3: 合成竖版公众号关注海报 (侧栏卡片用)"""
from PIL import Image, ImageDraw, ImageFont, ImageOps

SRC = r"E:\WorkSpace\微信公众号\线下物料素材\搜一搜公众号推广物料图片-png\扫码_搜索联合传播样式-标准色版.png"
OUT = r"E:\WorkBuddy\个人网站\source\img\wechat-poster.png"

GREEN = (7, 193, 96)      # 微信品牌绿
DARK = (38, 38, 38)
GRAY = (130, 130, 130)

img = Image.open(SRC).convert("RGB")
qr = img.crop((72, 58, 556, 549))          # 白卡+二维码, 484x491
qr = qr.resize((480, 486), Image.LANCZOS)  # 等比缩放

W = 600
PAD = 40
F_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 34)
F_NAME = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 44)
F_SUB = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 22)

H = 60 + 48 + 16 + 486 + 34 + 62 + 30 + 42 + 50
poster = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(poster)

t1 = "微信扫码关注公众号"
w1 = d.textlength(t1, font=F_TITLE)
d.text(((W - w1) / 2, 52), t1, font=F_TITLE, fill=GREEN)

poster.paste(qr, ((W - 480) // 2, 60 + 48 + 16))

t2 = "码尘飞扬社"
w2 = d.textlength(t2, font=F_NAME)
d.text(((W - w2) / 2, 60 + 48 + 16 + 486 + 34), t2, font=F_NAME, fill=DARK)

t3 = "ISP / 相机影像 / 开发随笔"
w3 = d.textlength(t3, font=F_SUB)
d.text(((W - w3) / 2, 60 + 48 + 16 + 486 + 34 + 62 + 30), t3, font=F_SUB, fill=GRAY)

poster.save(OUT)
print("海报已生成:", OUT, "尺寸:", poster.size)
