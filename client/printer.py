from reportlab.lib.pagesizes import A4              # ขนาดกระดาษ A4
from reportlab.lib import colors                    # สีสำหรับ PDF
from reportlab.lib.units import mm                  # หน่วยมิลลิเมตร
from reportlab.pdfgen import canvas                 # วาด PDF
from reportlab.pdfbase import pdfmetrics            # จัดการฟอนต์
from reportlab.pdfbase.ttfonts import TTFont        # โหลดฟอนต์ TTF
import os                                           # จัดการ path ไฟล์
import sys                                          # เปิดไฟล์ข้ามระบบ
import subprocess                                   # สั่งปริ้นบน Mac/Linux
import tempfile                                     # สร้างไฟล์ชั่วคราว
from datetime import datetime                       # วันเวลาปัจจุบัน

# ══════════════════════════════════════════════
#   ตั้งค่าฟอนต์ภาษาไทย
#   ต้องมีไฟล์ .ttf อยู่ในโฟลเดอร์ fonts/
#   ดาวน์โหลดฟรีได้จาก: fonts.google.com (Sarabun)
# ══════════════════════════════════════════════
BASE_DIR   = os.path.dirname(__file__)              # โฟลเดอร์ของ printer.py
FONTS_DIR  = os.path.join(BASE_DIR, "fonts")       # โฟลเดอร์ฟอนต์
ASSETS_DIR = os.path.join(BASE_DIR, "assets")      # โฟลเดอร์รูปภาพ

def register_fonts():
    """โหลดฟอนต์ภาษาไทยเข้า reportlab"""
    font_paths = {
        "Sarabun":      os.path.join(FONTS_DIR, "Sarabun-Regular.ttf"),
        "Sarabun-Bold": os.path.join(FONTS_DIR, "Sarabun-Bold.ttf"),
    }
    registered = []
    for name, path in font_paths.items():
        if os.path.exists(path):                    # ถ้ามีไฟล์ฟอนต์
            pdfmetrics.registerFont(TTFont(name, path))
            registered.append(name)
    return registered                               # คืนรายชื่อฟอนต์ที่โหลดได้

# ══════════════════════════════════════════════
#   สีที่ใช้ใน PDF
# ══════════════════════════════════════════════
PDF_COLOR = {
    "bg_dark":   colors.HexColor("#0d0b1e"),        # พื้นหลังหลัก
    "bg_card":   colors.HexColor("#1a1535"),        # พื้นหลัง card
    "purple":    colors.HexColor("#7c3aed"),        # ม่วงหลัก
    "gold":      colors.HexColor("#f59e0b"),        # ทอง
    "text":      colors.HexColor("#f3f0ff"),        # ข้อความหลัก
    "subtext":   colors.HexColor("#a78bfa"),        # ข้อความรอง
    "love":      colors.HexColor("#ec4899"),        # ชมพู
    "work":      colors.HexColor("#3b82f6"),        # น้ำเงิน
    "money":     colors.HexColor("#f59e0b"),        # ทอง
    "study":     colors.HexColor("#10b981"),        # เขียว
    "white":     colors.white,
    "black":     colors.black,
}

CATEGORY_COLOR = {
    "love":  PDF_COLOR["love"],
    "work":  PDF_COLOR["work"],
    "money": PDF_COLOR["money"],
    "study": PDF_COLOR["study"],
}

# ══════════════════════════════════════════════
#   ฟังก์ชันช่วย: วาดกล่องสี่เหลี่ยมมุมมน
# ══════════════════════════════════════════════
def draw_rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=None):
    """
    วาดสี่เหลี่ยมมุมมน
    c           = canvas
    x, y        = มุมล่างซ้าย
    w, h        = กว้าง, สูง
    r           = รัศมีมุมมน
    fill_color  = สีพื้น
    stroke_color= สีขอบ (None = ไม่มีขอบ)
    """
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(1.5)
    else:
        c.setStrokeColor(fill_color)

    p = c.beginPath()
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - 2*r, y, x + w, y + 2*r, -90, 90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - 2*r, y + h - 2*r, x + w, y + h, 0, 90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - 2*r, x + 2*r, y + h, 90, 90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + 2*r, y + 2*r, 180, 90)
    p.close()
    c.drawPath(p, fill=1, stroke=1 if stroke_color else 0)

# ══════════════════════════════════════════════
#   ฟังก์ชันช่วย: วาดข้อความไทย wrap อัตโนมัติ
# ══════════════════════════════════════════════
def draw_thai_text(c, text: str, x: float, y: float,
                   font: str, size: int, color,
                   max_width: float, line_height: float) -> float:
    """
    วาดข้อความไทยแบบ word wrap
    คืนค่า: y หลังจากวาดเสร็จ (สำหรับคำนวณตำแหน่งต่อไป)
    """
    c.setFillColor(color)
    c.setFont(font, size)

    words   = text.split(" ")           # แบ่งคำด้วยช่องว่าง
    line    = ""
    lines   = []

    for word in words:
        test = f"{line} {word}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            line = test                  # ยังใส่ได้ ต่อบรรทัด
        else:
            if line:
                lines.append(line)       # เต็มแล้ว บันทึกบรรทัดนี้
            line = word                  # เริ่มบรรทัดใหม่

    if line:
        lines.append(line)               # บรรทัดสุดท้าย

    for ln in lines:
        c.drawString(x, y, ln)          # วาดแต่ละบรรทัด
        y -= line_height                # เลื่อนลง

    return y                            # คืน y ปัจจุบัน

# ══════════════════════════════════════════════
#   ฟังก์ชันหลัก: สร้าง PDF ผลดวง
# ══════════════════════════════════════════════
def create_fortune_pdf(data: dict, output_path: str):
    """
    สร้าง PDF ผลทำนายดวงสไตล์พิกเซล
    รับ  : data (dict) ผลดวงจาก Server, output_path ที่จะบันทึก PDF
    """
    registered = register_fonts()                   # โหลดฟอนต์ไทย

    # เลือกฟอนต์ที่ใช้ได้
    if "Sarabun-Bold" in registered:
        font_bold   = "Sarabun-Bold"
        font_normal = "Sarabun"
    else:
        font_bold   = "Helvetica-Bold"              # fallback ถ้าไม่มีฟอนต์ไทย
        font_normal = "Helvetica"

    # ── สร้าง canvas ─────────────────────────
    c = canvas.Canvas(output_path, pagesize=A4)
    W, H = A4                                       # 595 x 842 pt

    margin   = 20 * mm                             # ขอบกระดาษ
    content_w = W - 2 * margin                     # ความกว้างเนื้อหา

    # ดึงข้อมูลจาก dict
    name      = data.get("name", "")
    birthdate = data.get("birthdate", "")
    zodiac    = data.get("zodiac", "")
    element   = data.get("element", "")
    trait     = data.get("trait", "")
    category  = data.get("category", "love")
    cat_th    = data.get("category_th", "")
    fortune   = data.get("fortune", "")
    lnum      = str(data.get("lucky_number", ""))
    lcolor    = data.get("lucky_color", "")
    lday      = data.get("lucky_day", "")
    lgem      = data.get("lucky_gem", "")
    litem     = data.get("lucky_item", "")
    gen_at    = data.get("generated_at", "")
    cat_color = CATEGORY_COLOR.get(category, PDF_COLOR["purple"])

    y = H                                           # เริ่มจากบนสุด

    # ══ 1. พื้นหลังทั้งหน้า ══════════════════
    draw_rounded_rect(c, 0, 0, W, H, 0, PDF_COLOR["bg_dark"])

    # ══ 2. Header ════════════════════════════
    header_h = 55 * mm
    draw_rounded_rect(c, 0, H - header_h, W, header_h, 0, PDF_COLOR["bg_card"])

    # เส้นขอบล่าง header
    c.setStrokeColor(cat_color)
    c.setLineWidth(3)
    c.line(0, H - header_h, W, H - header_h)

    # ชื่อแอป
    c.setFillColor(PDF_COLOR["gold"])
    c.setFont(font_bold, 22)
    c.drawCentredString(W/2, H - 18*mm, "✨  นำโชค Fortune Teller  ✨")

    # ชื่อหมวดหมู่
    c.setFillColor(cat_color)
    c.setFont(font_bold, 16)
    c.drawCentredString(W/2, H - 30*mm, f"~ {cat_th} ~")

    # ชื่อผู้ใช้ และราศี
    c.setFillColor(PDF_COLOR["subtext"])
    c.setFont(font_normal, 12)
    c.drawCentredString(W/2, H - 42*mm, f"{name}  |  {zodiac}  |  {element}  |  เกิด {birthdate}")

    y = H - header_h - 8*mm                        # y เริ่มต้นเนื้อหา

    # ══ 3. Card: รูปแมว + คำทำนาย ═══════════
    card_y     = y - 5*mm
    card_x     = margin
    fortune_card_h = 85*mm

    draw_rounded_rect(c, card_x, card_y - fortune_card_h,
                      content_w, fortune_card_h, 6*mm, PDF_COLOR["bg_card"])

    # เส้นขอบซ้าย card (สีหมวด)
    c.setStrokeColor(cat_color)
    c.setLineWidth(4)
    c.line(card_x + 3*mm, card_y - fortune_card_h + 5*mm,
           card_x + 3*mm, card_y - 5*mm)

    # หัวข้อ
    c.setFillColor(PDF_COLOR["gold"])
    c.setFont(font_bold, 14)
    c.drawString(card_x + 10*mm, card_y - 12*mm, "🔮  คำทำนายจากนำโชค")

    # เส้นคั่น
    c.setStrokeColor(PDF_COLOR["purple"])
    c.setLineWidth(0.5)
    c.line(card_x + 10*mm, card_y - 15*mm,
           card_x + content_w - 10*mm, card_y - 15*mm)

    # เนื้อหาคำทำนาย
    y_text = card_y - 20*mm
    y_text = draw_thai_text(
        c, fortune,
        card_x + 10*mm, y_text,
        font_normal, 11, PDF_COLOR["text"],
        content_w - 20*mm, 6.5*mm
    )

    y = card_y - fortune_card_h - 6*mm             # y หลัง card นี้

    # ══ 4. Card: สิ่งมงคล (Grid 3x2) ════════
    lucky_card_h = 52*mm
    draw_rounded_rect(c, card_x, y - lucky_card_h,
                      content_w, lucky_card_h, 6*mm, PDF_COLOR["bg_card"])

    # หัวข้อ
    c.setFillColor(PDF_COLOR["gold"])
    c.setFont(font_bold, 14)
    c.drawString(card_x + 10*mm, y - 10*mm, "🍀  สิ่งมงคลประจำตัว")

    c.setStrokeColor(PDF_COLOR["purple"])
    c.setLineWidth(0.5)
    c.line(card_x + 10*mm, y - 13*mm,
           card_x + content_w - 10*mm, y - 13*mm)

    # Grid 3 คอลัมน์ x 2 แถว
    lucky_data = [
        ("🔢 เลขมงคล",  lnum),
        ("🎨 สีมงคล",   lcolor),
        ("📅 วันมงคล",  lday),
        ("💎 พลอยมงคล", lgem),
        ("🎁 ของมงคล",  litem),
        ("⭐ นิสัย",    trait),
    ]
    cell_w = (content_w - 10*mm) / 3               # ความกว้างแต่ละช่อง
    cell_h = 14*mm
    grid_start_y = y - 17*mm
    grid_start_x = card_x + 5*mm

    for i, (label, value) in enumerate(lucky_data):
        col = i % 3                                 # คอลัมน์ 0-2
        row = i // 3                                # แถว 0-1
        cx  = grid_start_x + col * cell_w
        cy  = grid_start_y - row * (cell_h + 2*mm)

        # กล่อง cell
        draw_rounded_rect(
            c, cx, cy - cell_h, cell_w - 3*mm, cell_h,
            3*mm, colors.HexColor("#231d4a")
        )

        # label
        c.setFillColor(PDF_COLOR["subtext"])
        c.setFont(font_normal, 8)
        c.drawString(cx + 3*mm, cy - 5*mm, label)

        # value
        c.setFillColor(PDF_COLOR["text"])
        c.setFont(font_bold, 10)
        c.drawString(cx + 3*mm, cy - 11*mm, value)

    y = y - lucky_card_h - 6*mm                    # y หลัง card นี้

    # ══ 5. Footer ════════════════════════════
    footer_h = 18*mm
    draw_rounded_rect(c, 0, 0, W, footer_h, 0, PDF_COLOR["bg_card"])

    c.setStrokeColor(cat_color)
    c.setLineWidth(2)
    c.line(0, footer_h, W, footer_h)

    c.setFillColor(PDF_COLOR["subtext"])
    c.setFont(font_normal, 10)
    c.drawCentredString(W/2, 10*mm, f"ทำนายโดย นำโชค 🐱  •  {gen_at}  •  ขอให้โชคดีนะจ๊ะ ✨")

    # ══ 6. บันทึก PDF ════════════════════════
    c.save()

# ══════════════════════════════════════════════
#   ฟังก์ชันสั่งพิมพ์ (เรียกจาก client.py)
# ══════════════════════════════════════════════
def print_fortune_pdf(data: dict):
    """
    สร้าง PDF และเปิด dialog สั่งปริ้น
    รับ: data (dict) ผลดวงจาก Server
    """
    # สร้างชื่อไฟล์จากชื่อผู้ใช้ + timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_safe = data.get("name", "fortune").replace(" ", "_")
    filename  = f"fortune_{name_safe}_{timestamp}.pdf"

    # บันทึกในโฟลเดอร์เดียวกับ printer.py
    output_path = os.path.join(BASE_DIR, filename)

    create_fortune_pdf(data, output_path)           # สร้าง PDF
    print(f"✅ บันทึก PDF: {output_path}")

    # ── เปิด PDF ตามระบบปฏิบัติการ ───────────
    try:
        if sys.platform == "win32":                 # Windows
            os.startfile(output_path)               # เปิด dialog ปริ้น
        elif sys.platform == "darwin":              # macOS
            subprocess.run(["open", output_path])   # เปิดด้วย Preview
        else:                                       # Linux
            subprocess.run(["xdg-open", output_path])
        print(f"✅ เปิด PDF สำเร็จ")
    except Exception as e:
        print(f"⚠️ เปิดไฟล์ไม่สำเร็จ: {e}")
        print(f"   ไฟล์บันทึกที่: {output_path}")

    return output_path                              # คืน path ไฟล์ที่สร้าง

# ══════════════════════════════════════════════
#   ทดสอบ (รันไฟล์นี้โดยตรง)
# ══════════════════════════════════════════════
if __name__ == "__main__":
    # ข้อมูลตัวอย่างสำหรับทดสอบ
    test_data = {
        "name":          "สมชาย ใจดี",
        "birthdate":     "1998-08-15",
        "category":      "love",
        "category_th":   "ดวงความรัก ❤️",
        "zodiac":        "ราศีสิงห์ ♌",
        "element":       "ไฟ 🔥",
        "trait":         "มั่นใจ มีเสน่ห์ ชอบความสนใจ",
        "fortune":       "ฮัลโหลลล สมชาย ใจดี ชาวราศีสิงห์ ♌ ธาตุไฟตัวแม่ตัวมัม! แม่หมอขอทักเลยนะว่าช่วงนี้ออร่าความรักหนูพุ่งปรี๊ดดด! เสน่ห์แรงแบบต้านไม่อยู่ คนโสดเตรียมตัวเลยจ้า มีเกณฑ์คนโปรไฟล์ดีเข้ามาแจกขนมจีบแบบรัวๆ",
        "lucky_number":  7,
        "lucky_color":   "สีทอง ✨",
        "lucky_day":     "วันศุกร์ 💕",
        "lucky_gem":     "โรสควอตซ์ 💎",
        "lucky_item":    "ดอกไม้สีชมพู 🌸",
        "generated_at":  "06/03/2026 14:30",
    }

    path = print_fortune_pdf(test_data)
    print(f"\nสร้าง PDF สำเร็จที่: {path}")
