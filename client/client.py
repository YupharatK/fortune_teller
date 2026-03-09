# ══════════════════════════════════════════════════════════════════
#   client.py — โปรแกรมหลักฝั่งผู้ใช้ (GUI) ของแอปดูดวง "นำโชค"
#
#   โครงสร้างการทำงาน (Flow):
#     1. Welcome  → หน้าต้อนรับ แสดงชื่อแอป + ปุ่มเริ่ม
#     2. Form     → กรอกชื่อ วันเกิด เลือกหมวดดวง
#     3. Loading  → รอผลจาก Server พร้อม animation
#     4. Result   → แสดงผลดวง + สิ่งมงคล + ปุ่มพิมพ์ PDF
#     (Error Popup → แสดงเมื่อเกิดข้อผิดพลาดจาก Server)
#
#   เทคโนโลยี: CustomTkinter (GUI) + TCP Socket (เชื่อมต่อ Server)
#   สไตล์ UI: Pixel Art RPG (ขอบเหลี่ยม, สี retro, animation)
# ══════════════════════════════════════════════════════════════════

# ── Import Library ────────────────────────────────────────────────
import customtkinter as ctk            # GUI framework ที่ปรับแต่งจาก tkinter ให้ดูทันสมัย
from PIL import Image, ImageTk         # จัดการรูปภาพ (โหลด, resize)
import socket                          # สร้าง TCP connection เชื่อมต่อ Server
import json                            # แปลงข้อมูลระหว่าง dict <-> JSON string
import threading                       # รันงาน network ใน thread แยก ไม่ให้ GUI ค้าง
import os                              # จัดการ file path (หาโฟลเดอร์ assets/)
import tkinter as tk                   # ใช้ Canvas วาด scanline effect พื้นหลัง
from datetime import datetime          # ดึงวันที่ปัจจุบัน สำหรับปุ่ม [TODAY]

# ══════════════════════════════════════════════════════════════════
#   ตั้งค่าการเชื่อมต่อ Server
#   - แก้ SERVER_IP เป็น IP ของเครื่อง Server ที่ต้องการเชื่อมต่อ
#   - SERVER_PORT ต้องตรงกับที่ตั้งค่าใน server.py
# ══════════════════════════════════════════════════════════════════
SERVER_IP   = "127.0.0.1"             # IP ของ Server (127.0.0.1 = เครื่องตัวเอง)
SERVER_PORT = 9999                     # Port ที่ Server เปิดรอรับ
BUFFER_SIZE = 4096                     # ขนาดบัฟเฟอร์รับข้อมูลจาก Server (bytes)
ENCODING    = "utf-8"                  # รูปแบบ encoding ข้อความ

# ══════════════════════════════════════════════════════════════════
#   ตั้งค่าธีม Pixel Art RPG
#   - ธีมมืด สไตล์เกม retro
#   - ใช้สีโทนม่วง-ทอง เป็นหลัก
# ══════════════════════════════════════════════════════════════════
ctk.set_appearance_mode("dark")                # ธีมมืด
ctk.set_default_color_theme("dark-blue")       # สีพื้นฐานของ CustomTkinter

# dict เก็บรหัสสีทั้งหมดที่ใช้ในแอป (Hex Color)
COLOR = {
    # สีพื้นหลัง (เรียงจากมืดสุด → สว่างขึ้น)
    "bg":           "#0a0a12",    # พื้นหลังหน้าต่างหลัก (ดำอมน้ำเงิน)
    "frame":        "#0f0f1e",    # พื้นหลัง frame / input field
    "card":         "#141428",    # พื้นหลัง card (กล่องเนื้อหา)
    "card_inner":   "#0a0a1a",    # พื้นหลัง card ซ้อนใน / ปุ่มที่ยังไม่เลือก

    # สีขอบ (border)
    "border":       "#2a2a5a",    # ขอบปกติ (น้ำเงินม่วงเข้ม)
    "border_hi":    "#4a4aaa",    # ขอบ highlight (สว่างขึ้น)
    "border_gold":  "#b8860b",    # ขอบทอง (ใช้กับ header, card สำคัญ)

    # สีม่วง (Primary)
    "purple":       "#6644cc",    # ม่วงหลัก (ปุ่ม, progress bar)
    "purple_dark":  "#442288",    # ม่วงเข้ม (ปุ่มกด)
    "purple_hi":    "#8866ee",    # ม่วงสว่าง (hover)

    # สีทอง (Accent)
    "gold":         "#d4a017",    # ทองโบราณ (หัวข้อ, label)
    "gold_bright":  "#ffd700",    # ทองสว่าง (กระพริบ, เน้น)

    # สีข้อความ
    "text":         "#e8e4f0",    # ข้อความหลัก (ขาวอมม่วง)
    "text_dim":     "#8888aa",    # ข้อความหรี่ (footer, timestamp)
    "subtext":      "#9988cc",    # ข้อความรอง (คำอธิบาย, loading msg)

    # สีประจำหมวดดวง (ใช้เป็นสีขอบ/ปุ่มตามหมวดที่เลือก)
    "love":         "#cc3366",    # ดวงความรัก — ชมพูแดง
    "work":         "#2255bb",    # ดวงการงาน — น้ำเงิน (ไม่ได้ใช้แล้ว)
    "money":        "#aa8800",    # ดวงการเงิน — ทอง
    "study":        "#228844",    # ดวงการเรียน — เขียว

    # สี error
    "error":        "#cc2244",    # แดง — แสดงข้อผิดพลาด
}

# dict เก็บอักขระ Unicode สำหรับตกแต่ง UI สไตล์ pixel art
PIXEL = {
    # กรอบ box-drawing (ใช้เป็นขอบ card ตกแต่ง)
    "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",   # มุมบนซ้าย, บนขวา, ล่างซ้าย, ล่างขวา
    "h": "═", "v": "║",                             # เส้นนอน, เส้นตั้ง
    # บล็อกเติม (ใช้ใน progress bar)
    "full": "█", "dark": "▓", "med": "▒", "light": "░",
    # สัญลักษณ์ตกแต่ง
    "star": "★", "arrow": "►", "arrow_l": "◄",      # ดาว, ลูกศร
    "diamond": "◆", "cursor": "▌", "dot": "·",      # เพชร, cursor กระพริบ, จุด
}

# dict เก็บฟอนต์สำหรับแต่ละตำแหน่ง (ใช้ Courier New ทั้งหมด — monospace ดูคล้าย pixel)
FONT = {
    "title":      ("Courier New", 20, "bold"),       # ชื่อแอป / ชื่อหน้า
    "heading":    ("Courier New", 14, "bold"),       # หัวข้อ card
    "button":     ("Courier New", 13, "bold"),       # ข้อความบนปุ่มหลัก
    "label":      ("Courier New", 12, "bold"),       # label ฟอร์ม / ชื่อหมวด
    "body":       ("Courier New", 12, "normal"),     # เนื้อหา / คำทำนาย
    "small":      ("Courier New", 10, "normal"),     # ข้อความเล็ก
    "small_bold": ("Courier New", 10, "bold"),       # ข้อความเล็กตัวหนา
    "tiny":       ("Courier New", 9, "normal"),      # ข้อความจิ๋ว (กรอบตกแต่ง, footer)
}

# path ไปยังโฟลเดอร์ที่เก็บรูปภาพ (อยู่ข้างๆ ไฟล์นี้)
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# ══════════════════════════════════════════════════════════════════
#   ฟังก์ชัน TCP: ส่งข้อมูลไป Server และรับผลกลับมา
#
#   การทำงาน:
#     1. สร้าง TCP socket → เชื่อมต่อ Server
#     2. แปลง payload (dict) → JSON string → ส่งไป Server
#     3. รอรับผลลัพธ์ → แปลง JSON → dict → คืนกลับ
#
#   ถ้าเกิด error จะคืน dict ที่มี status="error" + message
# ══════════════════════════════════════════════════════════════════
def send_to_server(payload: dict) -> dict:
    """
    ส่งข้อมูลไป Server ผ่าน TCP Socket
    รับ  : payload (dict) — ข้อมูลที่จะส่ง เช่น {"action":"fortune", "name":"...", ...}
    คืนค่า: dict — ผลลัพธ์จาก Server หรือ error message
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # สร้าง TCP socket
    client.settimeout(10)                                         # timeout 10 วินาที ถ้ารอนานกว่านี้จะ error
    try:
        client.connect((SERVER_IP, SERVER_PORT))                  # เชื่อมต่อไปยัง Server
        msg = json.dumps(payload, ensure_ascii=False)             # แปลง dict → JSON (รองรับภาษาไทย)
        client.sendall(msg.encode(ENCODING))                      # ส่ง JSON ไป Server
        raw = client.recv(BUFFER_SIZE)                            # รอรับผลลัพธ์กลับมา
        return json.loads(raw.decode(ENCODING))                   # แปลง JSON → dict คืนกลับ
    except ConnectionRefusedError:
        # Server ไม่เปิดหรือ IP/Port ผิด
        return {"status": "error", "message": "❌ ไม่สามารถเชื่อมต่อ Server ได้\nกรุณาตรวจสอบว่า Server เปิดอยู่"}
    except TimeoutError:
        # Server ไม่ตอบภายใน 10 วินาที
        return {"status": "error", "message": "⏱️ Server ไม่ตอบสนอง\nกรุณาลองใหม่อีกครั้ง"}
    except Exception as e:
        # error อื่นๆ ที่ไม่คาดคิด
        return {"status": "error", "message": f"❌ เกิดข้อผิดพลาด: {e}"}
    finally:
        client.close()                                            # ปิด socket เสมอ ไม่ว่าจะสำเร็จหรือไม่

# ══════════════════════════════════════════════════════════════════
#   ฟังก์ชันโหลดรูปภาพจากโฟลเดอร์ assets/
#   ถ้าไม่มีไฟล์ → คืน None (UI จะแสดง emoji แทน)
# ══════════════════════════════════════════════════════════════════
def load_image(filename: str, size: tuple) -> ctk.CTkImage | None:
    """
    โหลดรูปจาก assets/ แล้ว resize ตาม size ที่กำหนด
    รับ  : filename — ชื่อไฟล์รูป เช่น "cat_idle.png"
           size     — ขนาด (กว้าง, สูง) เช่น (180, 180)
    คืนค่า: CTkImage หรือ None ถ้าไม่มีไฟล์
    """
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):          # ถ้าไม่มีไฟล์รูป
        return None                       # คืน None → UI จะ fallback เป็น emoji
    img = Image.open(path)                # เปิดรูปด้วย Pillow
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)  # แปลงเป็น CTkImage

# ══════════════════════════════════════════════════════════════════
#   Class หลัก: FortuneApp — แอปดูดวงนำโชค
#
#   สืบทอดจาก ctk.CTk (หน้าต่างหลักของ CustomTkinter)
#   จัดการทุกหน้าจอ, animation, และการเชื่อมต่อ Server
#
#   Flow การใช้งาน:
#     __init__() → show_welcome() → show_form() → submit_fortune()
#     → show_loading() → fetch_fortune() [Thread แยก]
#     → on_fortune_received() → show_result() หรือ show_error_popup()
# ══════════════════════════════════════════════════════════════════
class FortuneApp(ctk.CTk):

    def __init__(self):
        """
        เริ่มต้นแอป: ตั้งค่าหน้าต่าง + โหลดรูป + แสดงหน้า Welcome
        ถูกเรียกครั้งเดียวตอนเปิดโปรแกรม
        → ไปหน้า: show_welcome()
        """
        super().__init__()

        # ── ตั้งค่าหน้าต่างหลัก ──────────────────────
        self.title("★ นำโชค Fortune Teller ★")       # ชื่อหน้าต่าง (แสดงที่ title bar)
        self.geometry("700x800")                       # ขนาดหน้าต่าง 700x800 pixels
        self.resizable(False, False)                   # ล็อกขนาด ห้าม resize
        self.configure(fg_color=COLOR["bg"])           # สีพื้นหลังหน้าต่าง

        # ── ตัวแปรจัดการ animation ─────────────────
        # _screen_gen เป็นตัวนับ "รุ่น" ของหน้าจอ
        # ทุกครั้งที่เปลี่ยนหน้า จะ +1 ทำให้ animation ของหน้าเก่าหยุดทั้งหมด
        # ป้องกันบั๊ก: animation ของหน้าเก่าพยายามแก้ widget ที่ถูกลบไปแล้ว
        self._screen_gen = 0

        # ── ตัวแปรเก็บข้อมูลที่ผู้ใช้กรอกในฟอร์ม ──
        self.name_var     = ctk.StringVar()            # ชื่อ-นามสกุล
        self.birth_var    = ctk.StringVar()            # วันเกิด (YYYY-MM-DD)
        self.category_var = ctk.StringVar()            # หมวดดวงที่เลือก (love/money/study)
        self.fortune_data = {}                         # ผลดวงที่ได้จาก Server (dict)

        # ── โหลดรูปภาพจาก assets/ ─────────────────
        # รูปแมว 3 สถานะ: นั่งเฉย, คิด, เฉลย
        self.img_idle     = load_image("cat_idle.png",     (180, 180))   # หน้า Welcome + Form
        self.img_thinking = load_image("cat_thinking.png", (160, 160))   # หน้า Loading
        self.img_reveal   = load_image("cat_reveal.png",   (160, 160))   # หน้า Result
        # ไอคอนหมวดดวง (ใช้ในหน้า Form)
        self.img_love     = load_image("icon_love.png",    (50, 50))     # ไอคอนความรัก
        self.img_money    = load_image("icon_money.png",   (50, 50))     # ไอคอนการเงิน
        self.img_study    = load_image("icon_study.png",   (50, 50))     # ไอคอนการเรียน

        # ── แสดงหน้าแรก ───────────────────────────
        self.show_welcome()                            # → ไปหน้า Welcome

    # ══════════════════════════════════════════════════════════════
    #   clear_screen() — ล้าง widget ทั้งหมดออกจากหน้าจอ
    #
    #   เรียกทุกครั้งก่อนจะแสดงหน้าใหม่
    #   เพิ่ม _screen_gen เพื่อบอก animation ทั้งหมดให้หยุดทำงาน
    # ══════════════════════════════════════════════════════════════
    def clear_screen(self):
        """ลบ widget ทั้งหมด + หยุด animation ทั้งหมดของหน้าเก่า"""
        self._screen_gen += 1                          # +1 → animation เก่าจะเช็คแล้วหยุดเอง
        for widget in self.winfo_children():           # วนลูปทุก widget ในหน้าต่าง
            widget.destroy()                           # ลบทิ้ง

    # ══════════════════════════════════════════════════════════════
    #   add_scanline_bg() — วาดเส้น scanline เหมือนจอ CRT โบราณ
    #
    #   สร้าง Canvas ขนาดเท่าหน้าต่าง วาดเส้นนอนทุก 4 pixels
    #   แล้ววาง (place) ไว้ใต้ widget ทั้งหมด เป็น effect พื้นหลัง
    #   เรียกตอนต้นของทุกหน้า (หลัง clear_screen)
    # ══════════════════════════════════════════════════════════════
    def add_scanline_bg(self):
        """วาด scanline เบาๆ เป็นพื้นหลังเหมือนจอ CRT retro"""
        canvas = tk.Canvas(self, width=700, height=800,
                           bg=COLOR["bg"], highlightthickness=0)
        canvas.place(x=0, y=0)                         # วางเต็มหน้าจอ
        for y in range(0, 800, 4):                     # ทุก 4 pixel
            canvas.create_line(0, y, 700, y, fill="#111122", width=1)  # วาดเส้นนอนสีน้ำเงินจาง
        tk.Misc.lower(canvas)                          # ส่ง canvas ลงไปอยู่ใต้ widget อื่นทั้งหมด

    # ══════════════════════════════════════════════════════════════
    #   Animation: blink_widget() — ทำให้ widget กระพริบสลับ 2 สี
    #
    #   ใช้กับ: ปุ่ม "เริ่มดูดวง" (กระพริบทอง-ขาว),
    #          เพชรตกแต่ง (กระพริบทอง-หรี่)
    #
    #   หลักการ: ใช้ self.after() กำหนดเวลาเรียก _tick() วนซ้ำ
    #           เช็ค _screen_gen เพื่อหยุดเมื่อเปลี่ยนหน้า
    # ══════════════════════════════════════════════════════════════
    def blink_widget(self, widget, color_a: str, color_b: str,
                     interval_ms: int = 500, attr: str = "text_color"):
        """
        สลับสีของ widget ระหว่าง color_a กับ color_b ทุก interval_ms มิลลิวินาที
        widget      — widget ที่จะกระพริบ
        color_a/b   — สีสลับไปมา
        interval_ms — ความเร็วกระพริบ (ms)
        attr        — attribute ที่จะเปลี่ยนสี (เช่น "text_color", "border_color")
        """
        gen = self._screen_gen                         # จำรุ่นหน้าจอตอนเริ่ม
        state = {"flip": True}                         # True = แสดง color_a, False = color_b

        def _tick():
            if self._screen_gen != gen:                # ถ้าเปลี่ยนหน้าแล้ว → หยุด
                return
            try:
                widget.configure(**{attr: color_a if state["flip"] else color_b})
                state["flip"] = not state["flip"]      # สลับสถานะ
                self.after(interval_ms, _tick)          # นัดเรียกอีกครั้ง
            except Exception:
                pass                                   # widget ถูกลบไปแล้ว → หยุดเงียบ

        _tick()                                        # เริ่มกระพริบทันที

    # ══════════════════════════════════════════════════════════════
    #   Animation: typewriter_effect() — แสดงข้อความทีละตัวอักษร
    #
    #   ใช้กับ: หน้า Result — แสดงคำทำนายทีละตัว เหมือนพิมพ์ดีด
    #          มี cursor "▌" กระพริบอยู่ท้ายข้อความ
    #          เสร็จแล้วเรียก on_done callback
    #
    #   ความเร็ว: ช่องว่าง=เร็ว(8ms), เครื่องหมาย=ช้า(120ms), ปกติ=30ms
    # ══════════════════════════════════════════════════════════════
    def typewriter_effect(self, label, full_text: str,
                          delay_ms: int = 30, on_done=None):
        """
        แสดงข้อความทีละตัวอักษรบน label
        label     — CTkLabel ที่จะแสดงข้อความ
        full_text — ข้อความเต็มที่ต้องการแสดง
        delay_ms  — ความเร็วต่อตัวอักษร (ms)
        on_done   — ฟังก์ชันที่เรียกเมื่อพิมพ์ครบ
        """
        gen = self._screen_gen
        state = {"pos": 0, "running": True}            # pos=ตำแหน่งตัวอักษร, running=ยังทำงานอยู่
        self._typewriter_state = state                 # เก็บ reference ไว้ให้ _skip_typewriter เข้าถึง

        def _tick():
            if self._screen_gen != gen or not state["running"]:  # เปลี่ยนหน้า หรือถูก skip
                return
            pos = state["pos"]
            if pos > len(full_text):                   # พิมพ์ครบแล้ว
                try:
                    label.configure(text=full_text)    # แสดงข้อความเต็ม (เอา cursor ออก)
                except Exception:
                    pass
                if on_done:
                    on_done()                          # เรียก callback → _on_typewriter_done()
                return

            partial = full_text[:pos] + PIXEL["cursor"]  # ข้อความบางส่วน + cursor "▌"
            try:
                label.configure(text=partial)
            except Exception:
                return

            state["pos"] += 1
            # ปรับความเร็วตามชนิดตัวอักษร
            ch = full_text[pos - 1] if pos > 0 else ""
            if ch == " ":
                this_delay = 8                         # ช่องว่าง → เร็วมาก
            elif ch in ",.!?。\n":
                this_delay = 120                       # เครื่องหมาย → หยุดนิดนึง (dramatic)
            else:
                this_delay = delay_ms                  # ตัวอักษรปกติ → 30ms
            self.after(this_delay, _tick)

        _tick()

    # ══════════════════════════════════════════════════════════════
    #   Animation: animate_pixel_progress() — progress bar แบบ pixel
    #
    #   ใช้กับ: หน้า Loading — แสดง [████████░░░░]  60%
    #          วนซ้ำจาก 0% → 100% แล้วเริ่มใหม่ จนกว่าจะเปลี่ยนหน้า
    # ══════════════════════════════════════════════════════════════
    def animate_pixel_progress(self, label, total_blocks: int = 20,
                               interval_ms: int = 130):
        """
        แสดง progress bar แบบ pixel art บน label
        total_blocks — จำนวนบล็อกทั้งหมด (█ + ░)
        interval_ms  — ความเร็วต่อ step (ms)
        """
        gen = self._screen_gen
        state = {"filled": 0}                          # จำนวนบล็อกที่เติมแล้ว

        def _tick():
            if self._screen_gen != gen:
                return
            filled = state["filled"] % (total_blocks + 1)  # วนกลับเมื่อเต็ม
            empty  = total_blocks - filled
            bar    = f"[{'█' * filled}{'░' * empty}]"       # สร้างแถบ progress
            pct    = int((filled / total_blocks) * 100)     # คำนวณเปอร์เซ็นต์
            try:
                label.configure(text=f"{bar}  {pct:3d}%")
            except Exception:
                return
            state["filled"] += 1
            self.after(interval_ms, _tick)

        _tick()

    # ══════════════════════════════════════════════════════════════
    #   Animation: animate_cat_float() — แมวลอยขึ้นลงเบาๆ
    #
    #   ใช้กับ: รูปแมวในทุกหน้า — สลับ padding บน/ล่าง
    #          ทำให้แมวดูเหมือนลอยขึ้น-ลง (bobbing effect)
    # ══════════════════════════════════════════════════════════════
    def animate_cat_float(self, label, interval_ms: int = 850):
        """แมวลอยขึ้น-ลง โดยสลับ padding ของ label"""
        gen = self._screen_gen
        state = {"up": True}                           # True=ลอยขึ้น, False=ลงมา

        def _tick():
            if self._screen_gen != gen:
                return
            try:
                pady = (8, 18) if state["up"] else (18, 8)  # สลับ padding บน/ล่าง
                label.pack_configure(pady=pady)
                state["up"] = not state["up"]
                self.after(interval_ms, _tick)
            except Exception:
                pass

        _tick()

    # ══════════════════════════════════════════════════════════════
    #   Animation: animate_loading_messages() — วนข้อความขณะรอ
    #
    #   ใช้กับ: หน้า Loading — แสดงข้อความลึกลับสลับกัน
    #          เช่น "กำลังส่องลูกแก้ว..." → "คำนวณดวงดาว..." → ...
    # ══════════════════════════════════════════════════════════════
    def animate_loading_messages(self, label):
        """วนข้อความลึกลับ 7 ข้อความ ทุก 900ms"""
        messages = [
            "► นำโชคกำลังส่องลูกแก้ว...",
            "► กำลังคำนวณดวงดาว...",
            "► กำลังอ่านไพ่ทาโรต์...",
            "► ตรวจสอบโชคชะตา...",
            "► กำลังถอดรหัสจักรราศี...",
            "► เปิดสมุดดวงโบราณ...",
            "► ปลุกพลังคำทำนาย...",
        ]
        gen = self._screen_gen
        state = {"idx": 0}                             # index ข้อความปัจจุบัน

        def _tick():
            if self._screen_gen != gen:
                return
            try:
                label.configure(text=messages[state["idx"] % len(messages)])
                state["idx"] += 1                      # เลื่อนไปข้อความถัดไป (วนซ้ำ)
                self.after(900, _tick)
            except Exception:
                pass

        _tick()

    # ══════════════════════════════════════════════════════════════
    #   Animation: animate_stars_decoration() — ดาวเลื่อนเป็นลวดลาย
    #
    #   ใช้กับ: หน้า Welcome + Loading — แถบดาวตกแต่ง
    #          สลับรูปแบบ ★ ✦ ◆ ✦ ★ เพื่อให้ดูเคลื่อนไหว
    # ══════════════════════════════════════════════════════════════
    def animate_stars_decoration(self, label, interval_ms: int = 350):
        """วนลวดลายดาว 4 รูปแบบ ทุก 350ms"""
        patterns = [
            "★  ✦  ◆  ✦  ★  ✦  ◆  ✦  ★",
            "✦  ◆  ✦  ★  ✦  ◆  ✦  ★  ✦",
            "◆  ✦  ★  ✦  ◆  ✦  ★  ✦  ◆",
            "✦  ★  ✦  ◆  ✦  ★  ✦  ◆  ✦",
        ]
        gen = self._screen_gen
        state = {"idx": 0}

        def _tick():
            if self._screen_gen != gen:
                return
            try:
                label.configure(text=patterns[state["idx"] % len(patterns)])
                state["idx"] += 1
                self.after(interval_ms, _tick)
            except Exception:
                pass

        _tick()

    # ══════════════════════════════════════════════════════════════
    #   Component: make_pixel_header() — สร้าง header สไตล์ pixel
    #
    #   ใช้ร่วมกันทุกหน้า: แสดงรูปแมว + ชื่อหน้า + คำบรรยาย
    #   อยู่ใน frame สี่เหลี่ยมมุมฉาก มีขอบสี (สไตล์ pixel art)
    #   แมวมี float animation (ลอยขึ้นลง) ถ้า float_cat=True
    # ══════════════════════════════════════════════════════════════
    def make_pixel_header(self, parent, img, pixel_title: str = "",
                          thai_subtitle: str = "", border_color: str = None,
                          float_cat: bool = True):
        """
        สร้าง header frame พร้อมรูปแมว + ข้อความ
        parent        — widget แม่ที่จะวาง header
        img           — รูปแมว (CTkImage)
        pixel_title   — ชื่อหน้าภาษาอังกฤษ
        thai_subtitle — คำบรรยายภาษาไทย
        border_color  — สีขอบ frame (default = ทอง)
        float_cat     — แมวลอยขึ้นลงไหม
        คืนค่า: frame widget ที่สร้างขึ้น
        """
        if border_color is None:
            border_color = COLOR["border_gold"]

        # สร้าง frame ขอบเหลี่ยม (pixel art = corner_radius=0)
        frame = ctk.CTkFrame(parent, fg_color=COLOR["card"],
                             corner_radius=0, border_width=3,
                             border_color=border_color)
        frame.pack(fill="x", padx=15, pady=(12, 5))

        # รูปแมว (ถ้ามีรูป → ใช้รูป / ถ้าไม่มี → ใช้ emoji แทน)
        if img:
            cat_lbl = ctk.CTkLabel(frame, image=img, text="")
            cat_lbl.pack(pady=(12, 4))
            if float_cat:
                self.animate_cat_float(cat_lbl)        # เปิด animation ลอยขึ้นลง
        else:
            ctk.CTkLabel(frame, text="🐱",
                         font=("Courier New", 60)).pack(pady=(12, 4))

        # ชื่อหน้า (ภาษาอังกฤษ สีทอง)
        if pixel_title:
            ctk.CTkLabel(frame, text=pixel_title,
                         font=FONT["title"],
                         text_color=COLOR["gold"]).pack()

        # คำบรรยาย (ภาษาไทย สีม่วงอ่อน)
        if thai_subtitle:
            ctk.CTkLabel(frame, text=thai_subtitle,
                         font=FONT["body"],
                         text_color=COLOR["subtext"]).pack(pady=(3, 12))

        return frame

    # ══════════════════════════════════════════════════════════════
    #   หน้า 1: Welcome — หน้าต้อนรับ
    #
    #   แสดง: ดาวตกแต่ง (animated) + รูปแมว + ชื่อแอป + ปุ่มเริ่ม
    #   ปุ่มเริ่ม "►  เริ่มดูดวงกับนำโชค  ◄" กระพริบทอง-ขาว
    #
    #   → กดปุ่มเริ่ม → ไปหน้า: show_form()
    # ══════════════════════════════════════════════════════════════
    def show_welcome(self):
        """แสดงหน้าต้อนรับ → กดปุ่ม → ไป show_form()"""
        self.clear_screen()
        self.add_scanline_bg()

        # ── แถบดาวตกแต่ง (เคลื่อนไหว) ──────────
        stars_lbl = ctk.CTkLabel(self, text="★  ✦  ◆  ✦  ★  ✦  ◆  ✦  ★",
                                  font=FONT["small_bold"],
                                  text_color=COLOR["gold"])
        stars_lbl.pack(pady=(14, 0))
        self.animate_stars_decoration(stars_lbl)       # เริ่ม animation ดาว

        # ── Header: รูปแมว idle + ชื่อแอป ────────
        self.make_pixel_header(
            self, self.img_idle,
            pixel_title="★ FORTUNE TELLER ★",
            thai_subtitle="~ หมอดูแมวดำผู้ทรงพลัง ~",
            border_color=COLOR["border_gold"],
            float_cat=True                             # แมวลอยขึ้นลง
        )

        # ── ปุ่มเริ่มดูดวง (กระพริบ) ─────────────
        self.btn_start = ctk.CTkButton(
            self,
            text="►  เริ่มดูดวงกับนำโชค  ◄",
            font=FONT["button"],
            fg_color=COLOR["purple"],
            hover_color=COLOR["purple_hi"],
            border_width=3,
            border_color=COLOR["gold"],
            corner_radius=0,                           # มุมเหลี่ยม (pixel style)
            height=58,
            command=self.show_form                     # กดแล้ว → ไปหน้า Form
        )
        self.btn_start.pack(fill="x", padx=40, pady=15)
        # ทำให้ข้อความปุ่มกระพริบ ทอง↔ขาว ทุก 650ms
        self.blink_widget(self.btn_start, COLOR["gold_bright"], COLOR["text"], 650)

        # ── Footer: แสดง Server IP ────────────────
        ctk.CTkLabel(self,
                     text=f"SERVER: {SERVER_IP}:{SERVER_PORT}",
                     font=FONT["tiny"],
                     text_color=COLOR["text_dim"]).pack(pady=(0, 10))

    # ══════════════════════════════════════════════════════════════
    #   หน้า 2: Form — กรอกข้อมูลผู้ใช้
    #
    #   แสดง: ฟอร์มกรอกชื่อ + วันเกิด + เลือกหมวดดวง (3 หมวด)
    #   หมวดดวง: ❤ ความรัก, ★ การเงิน, ▲ การเรียน
    #
    #   → กดปุ่ม "ดูดวง" → ตรวจสอบข้อมูล → ไปหน้า: show_loading()
    #   → กดปุ่ม "BACK" → กลับไปหน้า: show_welcome()
    # ══════════════════════════════════════════════════════════════
    def show_form(self):
        """แสดงฟอร์มกรอกข้อมูล → กดดูดวง → ไป show_loading() → กลับ → show_welcome()"""
        self.clear_screen()
        self.add_scanline_bg()

        # ── Header: รูปแมว (ขนาดเล็กกว่าหน้า Welcome) ─────
        img_idle_sm = load_image("cat_idle.png", (110, 110))
        self.make_pixel_header(
            self, img_idle_sm,
            pixel_title="ENTER YOUR DATA",
            thai_subtitle="กรอกข้อมูลของคุณ",
            border_color=COLOR["border_gold"],
            float_cat=False                            # ไม่ลอย (หน้า Form ต้องการพื้นที่)
        )

        # ── ส่วน PLAYER INFO (กรอกชื่อ + วันเกิด) ─────
        # กรอบตกแต่ง box-drawing ด้านบน
        ctk.CTkLabel(self,
                     text="╔══════════════ PLAYER INFO ═══════════════╗",
                     font=FONT["tiny"],
                     text_color=COLOR["border_hi"]).pack(pady=(5, 0))

        # frame หลักของฟอร์ม
        form = ctk.CTkFrame(self, fg_color=COLOR["card"],
                            corner_radius=0, border_width=2,
                            border_color=COLOR["border_hi"])
        form.pack(fill="x", padx=15, pady=0)

        # ── ช่องกรอกชื่อ ──────────────────────────
        ctk.CTkLabel(form, text="► ชื่อ - นามสกุล",
                     font=FONT["label"],
                     text_color=COLOR["gold"]).pack(anchor="w", padx=15, pady=(12, 3))

        self.entry_name = ctk.CTkEntry(
            form, textvariable=self.name_var,           # ผูกกับ StringVar (เก็บค่าที่พิมพ์)
            placeholder_text="เช่น สมชาย ใจดี",        # ข้อความตัวอย่าง (หายไปเมื่อพิมพ์)
            font=FONT["body"], height=40,
            fg_color=COLOR["card_inner"],               # สีพื้นช่อง input
            border_color=COLOR["purple"],               # ขอบม่วง
            border_width=2,
            corner_radius=0                             # มุมเหลี่ยม (pixel style)
        )
        self.entry_name.pack(fill="x", padx=15, pady=(0, 10))

        # ── ช่องกรอกวันเกิด + ปุ่ม [TODAY] ───────
        ctk.CTkLabel(form, text="► วันเดือนปีเกิด  (YYYY-MM-DD)",
                     font=FONT["label"],
                     text_color=COLOR["gold"]).pack(anchor="w", padx=15, pady=(5, 3))

        birth_row = ctk.CTkFrame(form, fg_color="transparent")  # แถว: input + ปุ่ม TODAY
        birth_row.pack(fill="x", padx=15, pady=(0, 12))

        self.entry_birth = ctk.CTkEntry(
            birth_row, textvariable=self.birth_var,
            placeholder_text="เช่น 2000-08-15",
            font=FONT["body"], height=40,
            fg_color=COLOR["card_inner"],
            border_color=COLOR["purple"],
            border_width=2,
            corner_radius=0
        )
        self.entry_birth.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # ปุ่ม [TODAY] — กดแล้วกรอกวันนี้ให้อัตโนมัติ
        ctk.CTkButton(
            birth_row, text="[TODAY]",
            font=FONT["small_bold"],
            fg_color=COLOR["frame"],
            hover_color=COLOR["purple"],
            border_width=2, border_color=COLOR["border_hi"],
            corner_radius=0,
            width=90, height=40,
            command=lambda: self.birth_var.set(datetime.now().strftime("%Y-%m-%d"))
        ).pack(side="left")

        # กรอบตกแต่ง box-drawing ด้านล่าง
        ctk.CTkLabel(self,
                     text="╚═════════════════════════════════════════════╝",
                     font=FONT["tiny"],
                     text_color=COLOR["border_hi"]).pack(pady=(0, 4))

        # ── ส่วน SELECT QUEST (เลือกหมวดดวง) ──────
        ctk.CTkLabel(self,
                     text="╔══════════════ SELECT QUEST ══════════════╗",
                     font=FONT["tiny"],
                     text_color=COLOR["border_hi"]).pack(pady=(0, 0))

        quest_frame = ctk.CTkFrame(self, fg_color=COLOR["card"],
                                   corner_radius=0, border_width=2,
                                   border_color=COLOR["border_hi"])
        quest_frame.pack(fill="x", padx=15, pady=0)

        ctk.CTkLabel(quest_frame, text="► เลือกหมวดหมู่ที่ต้องการดูดวง",
                     font=FONT["label"],
                     text_color=COLOR["gold"]).pack(anchor="w", padx=15, pady=(10, 6))

        # สร้างปุ่มหมวดดวง 3 ปุ่ม (2 คอลัมน์)
        self.category_buttons = {}                     # เก็บ reference ปุ่มทั้งหมด
        cat_grid = ctk.CTkFrame(quest_frame, fg_color="transparent")
        cat_grid.pack(fill="x", padx=15, pady=(0, 12))

        # หมวดดวงที่เปิดให้เลือก (key, label, สี)
        categories = [
            ("love",  "❤  ความรัก",  COLOR["love"]),   # ชมพูแดง
            ("money", "★  การเงิน",  COLOR["money"]),   # ทอง
            ("study", "▲  การเรียน", COLOR["study"]),   # เขียว
        ]
        for i, (key, label, color) in enumerate(categories):
            btn = ctk.CTkButton(
                cat_grid, text=label,
                font=FONT["label"],
                fg_color=COLOR["card_inner"],           # ยังไม่เลือก → พื้นมืด
                hover_color=color,                      # hover → แสดงสีหมวด
                border_width=2, border_color=color,     # ขอบ = สีหมวด
                text_color=color,                       # ข้อความ = สีหมวด
                height=50, corner_radius=0,
                command=lambda k=key, c=color: self.select_category(k, c)  # กด → highlight ปุ่ม
            )
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="ew")
            cat_grid.grid_columnconfigure(i % 2, weight=1)
            self.category_buttons[key] = btn           # เก็บ reference ไว้ใช้ใน select_category

        # กรอบตกแต่ง box-drawing ด้านล่าง
        ctk.CTkLabel(self,
                     text="╚═════════════════════════════════════════════╝",
                     font=FONT["tiny"],
                     text_color=COLOR["border_hi"]).pack(pady=(0, 4))

        # ── label แสดง error (ว่างเปล่าตอนแรก) ───
        self.error_label = ctk.CTkLabel(self, text="",
                                         font=FONT["small"],
                                         text_color=COLOR["error"])
        self.error_label.pack(pady=(0, 3))

        # ── ปุ่มดูดวง ─────────────────────────────
        self.btn_submit = ctk.CTkButton(
            self,
            text="►  ให้นำโชคทำนายดวง!  ◄",
            font=FONT["button"],
            fg_color=COLOR["purple"],
            hover_color=COLOR["purple_hi"],
            border_width=3, border_color=COLOR["gold"],
            corner_radius=0, height=52,
            command=self.submit_fortune                # กด → ตรวจสอบ → ส่งไป Server
        )
        self.btn_submit.pack(fill="x", padx=40, pady=(5, 5))

        # ── ปุ่มย้อนกลับ → หน้า Welcome ──────────
        ctk.CTkButton(
            self, text="◄  BACK",
            font=FONT["small_bold"],
            fg_color="transparent",                    # ไม่มีพื้น (โปร่งใส)
            hover_color=COLOR["frame"],
            text_color=COLOR["text_dim"],
            corner_radius=0, height=30,
            command=self.show_welcome                  # กด → กลับหน้า Welcome
        ).pack(pady=(0, 8))

    # ══════════════════════════════════════════════════════════════
    #   select_category() — จัดการเมื่อผู้ใช้กดเลือกหมวดดวง
    #
    #   ปุ่มที่เลือก → เติมสีเต็ม (fg_color=สีหมวด)
    #   ปุ่มที่ไม่เลือก → คืนเป็นขอบอย่างเดียว
    # ══════════════════════════════════════════════════════════════
    def select_category(self, key: str, color: str):
        """
        highlight ปุ่มที่เลือก + บันทึกค่า key ลง category_var
        key   — ชื่อหมวด เช่น "love", "money", "study"
        color — สีหมวด เช่น "#cc3366"
        """
        self.category_var.set(key)                     # บันทึกหมวดที่เลือก
        cat_colors = {
            "love": COLOR["love"],
            "money": COLOR["money"], "study": COLOR["study"]
        }
        for k, btn in self.category_buttons.items():
            if k == key:
                # ปุ่มที่เลือก → เติมสีเต็ม ข้อความเป็นสีมืด
                btn.configure(fg_color=color, border_color=color,
                              text_color=COLOR["bg"], border_width=3)
            else:
                # ปุ่มที่ไม่เลือก → คืนเป็นพื้นมืด ขอบ+ข้อความ=สีหมวด
                c = cat_colors[k]
                btn.configure(fg_color=COLOR["card_inner"], border_color=c,
                              text_color=c, border_width=2)

    # ══════════════════════════════════════════════════════════════
    #   submit_fortune() — ตรวจสอบข้อมูล + ส่งไป Server
    #
    #   1. เช็คว่ากรอกครบไหม (ชื่อ, วันเกิด, หมวด)
    #   2. ถ้าไม่ครบ → แสดง error ใน error_label
    #   3. ถ้าครบ → ไปหน้า Loading + สร้าง Thread ส่งข้อมูลไป Server
    #
    #   → ไปหน้า: show_loading()
    #   → ส่งข้อมูลใน Thread: fetch_fortune()
    # ══════════════════════════════════════════════════════════════
    def submit_fortune(self):
        """ตรวจสอบ input → ส่งไป Server → ไป show_loading()"""
        name      = self.name_var.get().strip()        # ดึงค่าจาก StringVar
        birthdate = self.birth_var.get().strip()
        category  = self.category_var.get().strip()

        # ── ตรวจสอบข้อมูล (Validation) ────────────
        if not name:
            self.error_label.configure(text="⚠  กรุณากรอกชื่อ-นามสกุล")
            return                                     # หยุด ไม่ส่ง
        if not birthdate:
            self.error_label.configure(text="⚠  กรุณากรอกวันเดือนปีเกิด")
            return
        if not category:
            self.error_label.configure(text="⚠  กรุณาเลือกหมวดหมู่ดวง")
            return

        self.error_label.configure(text="")            # ล้าง error เก่า
        self.show_loading()                            # → ไปหน้า Loading ทันที

        # ส่งข้อมูลไป Server ใน Thread แยก (ไม่ให้ GUI ค้าง)
        threading.Thread(
            target=self.fetch_fortune,                 # ฟังก์ชันที่จะรันใน Thread
            args=(name, birthdate, category),          # ข้อมูลที่ส่งไป
            daemon=True                                # ปิด Thread อัตโนมัติเมื่อปิดโปรแกรม
        ).start()

    # ══════════════════════════════════════════════════════════════
    #   fetch_fortune() — ส่งข้อมูลไป Server (รันใน Thread แยก)
    #
    #   เรียก send_to_server() → รอผล → ส่งผลกลับมาที่ main thread
    #   ใช้ self.after(0, ...) เพื่ออัปเดต GUI จาก main thread
    #   (GUI ของ tkinter ห้ามแก้ไขจาก Thread อื่น)
    #
    #   → ส่งผลไปที่: on_fortune_received()
    # ══════════════════════════════════════════════════════════════
    def fetch_fortune(self, name: str, birthdate: str, category: str):
        """รันใน Thread: ส่งข้อมูลไป Server แล้วส่งผลกลับ main thread"""
        result = send_to_server({
            "action":    "fortune",                    # บอก Server ว่าต้องการดูดวง
            "name":      name,                         # ชื่อผู้ใช้
            "birthdate": birthdate,                    # วันเกิด
            "category":  category,                     # หมวดดวง
        })
        # after(0, ...) = กลับไปรันใน main thread โดยเร็วที่สุด
        self.after(0, lambda: self.on_fortune_received(result))

    # ══════════════════════════════════════════════════════════════
    #   on_fortune_received() — จัดการผลลัพธ์จาก Server
    #
    #   ถ้าสำเร็จ (status="success") → เก็บข้อมูล → ไปหน้า Result
    #   ถ้า error → แสดง popup error → กลับหน้า Form
    #
    #   → สำเร็จ → ไปหน้า: show_result()
    #   → error  → ไปหน้า: show_error_popup() → show_form()
    # ══════════════════════════════════════════════════════════════
    def on_fortune_received(self, result: dict):
        """จัดการผลจาก Server: สำเร็จ → show_result() / error → show_error_popup()"""
        if result.get("status") == "success":
            self.fortune_data = result                 # เก็บผลดวงทั้ง dict
            self.show_result()                         # → ไปหน้า Result
        else:
            # รวบรวม error message
            errors    = result.get("errors", {})
            error_msg = result.get("message", "")
            if errors:
                error_msg = "\n".join(f"• {v}" for v in errors.values())
            self.show_error_popup(error_msg)           # → แสดง popup error

    # ══════════════════════════════════════════════════════════════
    #   หน้า 3: Loading — รอผลจาก Server
    #
    #   แสดง: ดาวตกแต่ง + แมว thinking (ลอย) + ข้อความลึกลับหมุน
    #         + pixel progress bar [████░░░░] + เพชรกระพริบ
    #
    #   หน้านี้แสดงขณะรอ fetch_fortune() ใน Thread
    #   เมื่อได้ผล → on_fortune_received() จะเปลี่ยนหน้าอัตโนมัติ
    # ══════════════════════════════════════════════════════════════
    def show_loading(self):
        """แสดงหน้า Loading ขณะรอผลจาก Server"""
        self.clear_screen()
        self.add_scanline_bg()

        # ── ดาวตกแต่ง (animated) ──────────────────
        stars = ctk.CTkLabel(self, text="★  ✦  ◆  ✦  ★  ✦  ◆  ✦  ★",
                              font=FONT["small_bold"], text_color=COLOR["gold"])
        stars.pack(pady=(16, 0))
        self.animate_stars_decoration(stars)

        # ── Header: แมว thinking (ลอยขึ้นลง) ─────
        self.make_pixel_header(
            self, self.img_thinking,
            pixel_title="READING YOUR DESTINY...",
            thai_subtitle="กำลังทำนายดวง",
            border_color=COLOR["purple"],
            float_cat=True
        )

        # ── กล่องข้อความลึกลับ (หมุนเปลี่ยน) ─────
        ctk.CTkLabel(self,
                     text="╔══════════════════════════════════════════╗",
                     font=FONT["tiny"], text_color=COLOR["border_hi"]).pack(pady=(8, 0))

        msg_frame = ctk.CTkFrame(self, fg_color=COLOR["card"],
                                  corner_radius=0, border_width=2,
                                  border_color=COLOR["border_hi"])
        msg_frame.pack(fill="x", padx=15, pady=0)

        self.loading_msg_label = ctk.CTkLabel(
            msg_frame, text="► นำโชคกำลังส่องลูกแก้ว...",
            font=FONT["body"], text_color=COLOR["subtext"]
        )
        self.loading_msg_label.pack(pady=12)
        self.animate_loading_messages(self.loading_msg_label)  # เริ่มวนข้อความ

        ctk.CTkLabel(self,
                     text="╚══════════════════════════════════════════╝",
                     font=FONT["tiny"], text_color=COLOR["border_hi"]).pack(pady=(0, 15))

        # ── Pixel Progress Bar ────────────────────
        self.progress_label = ctk.CTkLabel(
            self, text="[░░░░░░░░░░░░░░░░░░░░]    0%",
            font=FONT["small_bold"], text_color=COLOR["purple_hi"]
        )
        self.progress_label.pack(pady=5)
        self.animate_pixel_progress(self.progress_label)       # เริ่ม animation progress

        # ── เพชรกระพริบ (ตกแต่ง) ──────────────────
        dots_lbl = ctk.CTkLabel(self, text="◆    ◆    ◆    ◆    ◆",
                                 font=FONT["small_bold"], text_color=COLOR["gold"])
        dots_lbl.pack(pady=12)
        self.blink_widget(dots_lbl, COLOR["gold"], COLOR["text_dim"], 700)

    # ══════════════════════════════════════════════════════════════
    #   หน้า 4: Result — แสดงผลดวง
    #
    #   แสดง: Header (แมว reveal + ชื่อหมวด + ชื่อผู้ใช้ + ราศี)
    #         + คำทำนาย (typewriter effect — พิมพ์ทีละตัว)
    #         + สิ่งมงคล 6 อย่าง (grid 2 คอลัมน์)
    #         + ราศี + timestamp
    #         + ปุ่มพิมพ์ PDF / ดูดวงอีกครั้ง
    #
    #   → กด [PDF] → เรียก print_fortune() → สร้าง PDF เปิด Preview
    #   → กด "ดูดวงอีกครั้ง" → กลับไปหน้า: show_form()
    # ══════════════════════════════════════════════════════════════
    def show_result(self):
        """แสดงผลดวง + typewriter → [PDF] / ดูดวงอีก → show_form()"""
        self.clear_screen()
        self.add_scanline_bg()
        d = self.fortune_data                          # dict ผลดวงจาก Server

        # ── กำหนดสีและไอคอนตามหมวด ────────────────
        cat_key   = d.get("category", "love")          # key หมวด (love/money/study)
        cat_color = COLOR.get(cat_key, COLOR["purple"])  # สีหมวด
        cat_icons = {"love": "❤", "work": "♦", "money": "★", "study": "▲"}
        cat_icon  = cat_icons.get(cat_key, "◆")        # ไอคอนหมวด

        # ── Header: แมว reveal + ข้อมูลผู้ใช้ ─────
        header_frame = ctk.CTkFrame(self, fg_color=COLOR["card"],
                                     corner_radius=0, border_width=3,
                                     border_color=cat_color)         # ขอบ = สีหมวด
        header_frame.pack(fill="x", padx=15, pady=(12, 5))

        if self.img_reveal:
            cat_lbl = ctk.CTkLabel(header_frame, image=self.img_reveal, text="")
            cat_lbl.pack(pady=(10, 4))
            self.animate_cat_float(cat_lbl)            # แมวลอย

        ctk.CTkLabel(header_frame, text="FORTUNE REVEALED!",
                     font=FONT["heading"], text_color=COLOR["gold"]).pack()

        # ชื่อหมวดดวง (เช่น "❤  ผลดวงความรัก  ❤")
        ctk.CTkLabel(header_frame,
                     text=f"{cat_icon}  ผลดวง{d.get('category_th', '')}  {cat_icon}",
                     font=FONT["label"], text_color=cat_color).pack()

        # ข้อมูลผู้ใช้ (ชื่อ | ราศี | ธาตุ)
        ctk.CTkLabel(header_frame,
                     text=f"สำหรับ {d.get('name', '')}  |  {d.get('zodiac', '')}  {d.get('element', '')}",
                     font=FONT["body"], text_color=COLOR["text_dim"]).pack(pady=(2, 10))

        # ── พื้นที่เลื่อนดู (Scrollable) ──────────
        # ใช้ CTkScrollableFrame เพราะเนื้อหาอาจยาวเกินหน้าจอ
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=COLOR["bg"],
            corner_radius=0, border_width=2,
            border_color=COLOR["border"],
            scrollbar_button_color=COLOR["purple"],
            scrollbar_button_hover_color=COLOR["purple_hi"]
        )
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        # ── Card: คำทำนาย (Typewriter Effect) ─────
        ctk.CTkLabel(scroll,
                     text="╔══════════════ YOUR DESTINY ═══════════════╗",
                     font=FONT["tiny"], text_color=COLOR["border_gold"]).pack(pady=(8, 0))

        fortune_card = ctk.CTkFrame(scroll, fg_color=COLOR["card"],
                                     corner_radius=0, border_width=2,
                                     border_color=COLOR["border_gold"])
        fortune_card.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(fortune_card, text="◆  คำทำนายจากนำโชค",
                     font=FONT["label"], text_color=COLOR["gold"]).pack(
            anchor="w", padx=15, pady=(10, 5))

        # Label สำหรับ typewriter — เริ่มต้นแสดง cursor "▌" อย่างเดียว
        self.fortune_label = ctk.CTkLabel(
            fortune_card, text=PIXEL["cursor"],
            font=FONT["body"],
            text_color=COLOR["text"],
            wraplength=570, justify="left"             # ตัดบรรทัดที่ 570px
        )
        self.fortune_label.pack(padx=15, pady=(0, 10), anchor="w")

        # ปุ่ม [SKIP] — กดข้ามไปแสดงคำทำนายทั้งหมดทันที
        self.btn_skip = ctk.CTkButton(
            fortune_card, text="[ SKIP ]",
            font=FONT["tiny"],
            fg_color=COLOR["frame"],
            hover_color=COLOR["border_hi"],
            border_width=1, border_color=COLOR["border_hi"],
            corner_radius=0, width=70, height=24,
            command=self._skip_typewriter              # กด → หยุด typewriter แสดงเต็ม
        )
        self.btn_skip.pack(anchor="e", padx=15, pady=(0, 8))

        ctk.CTkLabel(scroll,
                     text="╚═══════════════════════════════════════════╝",
                     font=FONT["tiny"], text_color=COLOR["border_gold"]).pack(pady=(0, 8))

        # ── Card: สิ่งมงคล (Grid 2 คอลัมน์ x 3 แถว) ─────
        ctk.CTkLabel(scroll,
                     text="╔══════════════ LUCKY ITEMS ════════════════╗",
                     font=FONT["tiny"], text_color=COLOR["border_hi"]).pack(pady=(0, 0))

        lucky_card = ctk.CTkFrame(scroll, fg_color=COLOR["card"],
                                   corner_radius=0, border_width=2,
                                   border_color=COLOR["border_hi"])
        lucky_card.pack(fill="x", pady=0)

        ctk.CTkLabel(lucky_card, text="◆  สิ่งมงคลประจำตัว",
                     font=FONT["label"], text_color=COLOR["gold"]).pack(
            anchor="w", padx=15, pady=(10, 6))

        # ข้อมูลสิ่งมงคล 6 อย่าง: เลข, สี, วัน, พลอย, ของ, นิสัย
        lucky_items = [
            ("◆ เลขมงคล",  str(d.get("lucky_number", "-"))),
            ("◆ สีมงคล",   d.get("lucky_color", "-")),
            ("◆ วันมงคล",  d.get("lucky_day", "-")),
            ("◆ พลอยมงคล", d.get("lucky_gem", "-")),
            ("◆ ของมงคล",  d.get("lucky_item", "-")),
            ("◆ นิสัย",    d.get("trait", "-")),
        ]

        lucky_grid = ctk.CTkFrame(lucky_card, fg_color="transparent")
        lucky_grid.pack(fill="x", padx=10, pady=(0, 10))

        # สร้าง cell สำหรับแต่ละสิ่งมงคล (2 คอลัมน์)
        for i, (label, value) in enumerate(lucky_items):
            cell = ctk.CTkFrame(lucky_grid, fg_color=COLOR["card_inner"],
                                corner_radius=0, border_width=2,
                                border_color=cat_color)            # ขอบ = สีหมวด
            cell.grid(row=i // 2, column=i % 2, padx=4, pady=4, sticky="ew")
            lucky_grid.grid_columnconfigure(i % 2, weight=1)

            # ชื่อสิ่งมงคล (ด้านบน เล็ก หรี่)
            ctk.CTkLabel(cell, text=label, font=FONT["tiny"],
                         text_color=COLOR["subtext"]).pack(anchor="w", padx=10, pady=(6, 1))
            # ค่าสิ่งมงคล (ด้านล่าง ใหญ่ สว่าง)
            ctk.CTkLabel(cell, text=value, font=FONT["label"],
                         text_color=COLOR["text"]).pack(anchor="w", padx=10, pady=(0, 6))

        ctk.CTkLabel(scroll,
                     text="╚═══════════════════════════════════════════╝",
                     font=FONT["tiny"], text_color=COLOR["border_hi"]).pack(pady=(0, 8))

        # ── Card: ราศีของผู้ใช้ ────────────────────
        zodiac_card = ctk.CTkFrame(scroll, fg_color=COLOR["card"],
                                    corner_radius=0, border_width=2,
                                    border_color=COLOR["border"])
        zodiac_card.pack(fill="x", padx=0, pady=(0, 8))

        ctk.CTkLabel(zodiac_card,
                     text=f"♈  ราศีของคุณ: {d.get('zodiac', '')}  |  {d.get('element', '')}",
                     font=FONT["label"], text_color=COLOR["subtext"]).pack(padx=15, pady=10)

        # ── Timestamp ─────────────────────────────
        ctk.CTkLabel(scroll,
                     text=f"ทำนายโดย นำโชค ★  เวลา {d.get('generated_at', '')}",
                     font=FONT["tiny"], text_color=COLOR["text_dim"]).pack(pady=5)

        # ── ปุ่มด้านล่าง (พิมพ์ PDF / ดูดวงอีก) ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=8)

        # ปุ่มพิมพ์ PDF → เรียก print_fortune() → สร้าง PDF + เปิด Preview
        ctk.CTkButton(
            btn_frame, text="[PDF]  พิมพ์ผลดวง",
            font=FONT["button"],
            fg_color=COLOR["gold"], hover_color=COLOR["border_gold"],
            text_color=COLOR["bg"],
            corner_radius=0, border_width=2, border_color=COLOR["gold_bright"],
            height=48,
            command=self.print_fortune                 # → print_fortune()
        ).pack(side="left", expand=True, padx=(0, 4))

        # ปุ่มดูดวงอีกครั้ง → กลับไปหน้า Form
        ctk.CTkButton(
            btn_frame, text="►  ดูดวงอีกครั้ง",
            font=FONT["button"],
            fg_color=COLOR["purple"], hover_color=COLOR["purple_hi"],
            corner_radius=0, border_width=3, border_color=COLOR["gold"],
            height=48,
            command=self.show_form                     # → กลับหน้า Form
        ).pack(side="left", expand=True, padx=(4, 0))

        # ── เริ่ม typewriter หลัง 600ms ───────────
        # รอ 600ms ก่อนเริ่มพิมพ์ (ให้ผู้ใช้เห็นหน้าก่อน)
        fortune_text = d.get("fortune", "")
        self._fortune_full_text = fortune_text         # เก็บไว้ให้ skip ใช้
        self.after(600, lambda: self.typewriter_effect(
            self.fortune_label, fortune_text,
            delay_ms=25,
            on_done=self._on_typewriter_done           # เสร็จแล้ว → ซ่อนปุ่ม SKIP
        ))

    # ══════════════════════════════════════════════════════════════
    #   _skip_typewriter() — ข้าม typewriter แสดงข้อความเต็มทันที
    #   เรียกจากปุ่ม [SKIP] ในหน้า Result
    # ══════════════════════════════════════════════════════════════
    def _skip_typewriter(self):
        """กดปุ่ม [SKIP] → หยุด typewriter → แสดงข้อความเต็ม"""
        if hasattr(self, "_typewriter_state"):
            self._typewriter_state["running"] = False  # บอก typewriter ให้หยุด
        try:
            self.fortune_label.configure(text=self._fortune_full_text)  # แสดงข้อความเต็ม
        except Exception:
            pass
        self._on_typewriter_done()                     # → ซ่อนปุ่ม SKIP

    # ══════════════════════════════════════════════════════════════
    #   _on_typewriter_done() — เรียกเมื่อ typewriter พิมพ์ครบ
    #   ซ่อนปุ่ม [SKIP] + แสดงข้อความเต็ม (เอา cursor ออก)
    # ══════════════════════════════════════════════════════════════
    def _on_typewriter_done(self):
        """typewriter เสร็จ → ซ่อน [SKIP] + แสดงข้อความเต็ม"""
        try:
            self.fortune_label.configure(text=self._fortune_full_text)
            self.btn_skip.pack_forget()                # ซ่อนปุ่ม SKIP (ไม่ลบ แค่ซ่อน)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    #   show_error_popup() — แสดง popup แจ้ง error สไตล์ pixel art
    #
    #   แสดง: กรอบ box-drawing สีแดง + ข้อความ error + ปุ่ม [OK]
    #   ใช้ grab_set() บังคับให้ปิด popup ก่อนใช้งานต่อ
    #
    #   → กด [OK] → ปิด popup + กลับไปหน้า: show_form()
    # ══════════════════════════════════════════════════════════════
    def show_error_popup(self, message: str):
        """แสดง popup error → กด OK → กลับ show_form()"""
        popup = ctk.CTkToplevel(self)                  # สร้างหน้าต่างใหม่ซ้อนทับ
        popup.title("ERROR")
        popup.geometry("440x290")
        popup.resizable(False, False)
        popup.configure(fg_color=COLOR["bg"])
        popup.grab_set()                               # บังคับให้ปิด popup ก่อน

        # กรอบตกแต่ง box-drawing สีแดง
        ctk.CTkLabel(popup,
                     text="╔════════════════════════╗",
                     font=FONT["small"], text_color=COLOR["error"]).pack(pady=(20, 0))

        ctk.CTkLabel(popup,
                     text="║   ⚠  SYSTEM ERROR  ⚠   ║",
                     font=FONT["small_bold"], text_color=COLOR["error"]).pack()

        ctk.CTkLabel(popup,
                     text="╚════════════════════════╝",
                     font=FONT["small"], text_color=COLOR["error"]).pack(pady=(0, 12))

        # ข้อความ error (ภาษาไทย)
        ctk.CTkLabel(popup, text=message,
                     font=FONT["body"], text_color="#ff7777",
                     wraplength=380, justify="center").pack(padx=20)

        # ปุ่ม [OK] → ปิด popup + กลับหน้า Form
        ctk.CTkButton(
            popup, text="[ OK ]",
            font=FONT["button"],
            fg_color=COLOR["error"],
            hover_color="#991133",
            text_color=COLOR["text"],
            corner_radius=0, border_width=2, border_color="#ff5555",
            width=120, height=42,
            command=lambda: [popup.destroy(), self.show_form()]  # ปิด popup → กลับ Form
        ).pack(pady=18)

    # ══════════════════════════════════════════════════════════════
    #   print_fortune() — สร้าง PDF ผลดวง + เปิดดู
    #
    #   เรียก printer.py → print_fortune_pdf() → สร้างไฟล์ PDF
    #   → เปิดด้วย Preview (macOS) / PDF viewer
    #   ถ้าไม่พบ printer.py หรือเกิด error → แสดง popup error
    # ══════════════════════════════════════════════════════════════
    def print_fortune(self):
        """สร้าง PDF ผลดวง → เปิด Preview / แสดง error ถ้าล้มเหลว"""
        try:
            from printer import print_fortune_pdf      # import ฟังก์ชันจาก printer.py
            print_fortune_pdf(self.fortune_data)       # ส่งผลดวงไปสร้าง PDF
        except ImportError:
            self.show_error_popup("❌ ไม่พบไฟล์ printer.py\nกรุณาตรวจสอบว่ามีไฟล์ครบ")
        except Exception as e:
            self.show_error_popup(f"❌ ปริ้นไม่สำเร็จ:\n{e}")


# ══════════════════════════════════════════════════════════════════
#   จุดเริ่มต้นโปรแกรม
#   สร้าง instance ของ FortuneApp แล้วเริ่ม event loop
#   (event loop = วนรอรับ input จากผู้ใช้ เช่น กดปุ่ม, พิมพ์ข้อมูล)
# ══════════════════════════════════════════════════════════════════
def main():
    app = FortuneApp()                                 # สร้างแอป → เรียก __init__() → show_welcome()
    app.mainloop()                                     # เริ่ม event loop (โปรแกรมรันวนอยู่ตรงนี้)

main()                                                 # เรียก main() เมื่อรันไฟล์นี้
