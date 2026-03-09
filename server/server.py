import socket                          # ใช้สำหรับการสื่อสารผ่านเครือข่าย
import json                            # ใช้สำหรับแปลงข้อมูลเป็น JSON
import threading                       # ใช้สำหรับรองรับ Client หลายคนพร้อมกัน
import sys                             # ใช้สำหรับออกจากโปรแกรม
import os                              # ใช้สำหรับจัดการ path ไฟล์

sys.path.insert(0, os.path.dirname(__file__))   # เพิ่ม path เพื่อ import ไฟล์ในโฟลเดอร์เดียวกัน
from fortune_engine import generate_fortune      # import ฟังก์ชันทำนายดวง
from validator import validate_all               # import ฟังก์ชันตรวจสอบ input

# ══════════════════════════════════════════════
#   ตั้งค่า Server (แก้ไขได้ที่นี่เลย)
# ══════════════════════════════════════════════
HOST        = "0.0.0.0"   # IP ที่ Server รับการเชื่อมต่อ ("0.0.0.0" = รับทุก IP)
PORT        = 9999         # Port ที่ใช้ (Client ต้องใช้ Port เดียวกัน)
BUFFER_SIZE = 4096         # ขนาดบัฟเฟอร์รับข้อมูล (bytes)
ENCODING    = "utf-8"      # รูปแบบ encoding ข้อความ

# ══════════════════════════════════════════════
#   ฟังก์ชันสร้าง Server Socket
# ══════════════════════════════════════════════
def create_server():
    server = socket.socket(
        socket.AF_INET,                # ใช้ IPv4
        socket.SOCK_STREAM             # ใช้ TCP (ข้อมูลครบ ไม่หาย ไม่ซ้ำ)
    )
    server.setsockopt(
        socket.SOL_SOCKET,             # ตั้งค่า socket ระดับ OS
        socket.SO_REUSEADDR, 1         # ให้ใช้ Port เดิมซ้ำได้ทันที (ไม่ต้องรอ)
    )
    server.bind((HOST, PORT))          # ผูก IP กับ Port เข้าด้วยกัน
    server.listen(5)                   # รอรับการเชื่อมต่อได้สูงสุด 5 คนในคิว
    print(f"🐱 นำโชค Server เริ่มทำงานที่ {HOST}:{PORT}")
    print("รอ Client เชื่อมต่อ... (กด Ctrl+C เพื่อหยุด)\n")
    return server                      # ส่ง server socket กลับไปใช้งาน

# ══════════════════════════════════════════════
#   ฟังก์ชันส่งข้อมูล JSON กลับไปหา Client
# ══════════════════════════════════════════════
def send_response(client_socket, data):
    payload = json.dumps(data, ensure_ascii=False) + "\n"  # แปลง dict → JSON string
    client_socket.sendall(payload.encode(ENCODING))        # ส่งข้อมูลทั้งหมดไปยัง Client

# ══════════════════════════════════════════════
#   ฟังก์ชันรับข้อมูล JSON จาก Client
# ══════════════════════════════════════════════
def receive_request(client_socket):
    raw = client_socket.recv(BUFFER_SIZE)    # รับข้อมูลจาก Client (bytes)
    if not raw:                              # ถ้าได้ข้อมูลว่าง แสดงว่า Client ตัดการเชื่อมต่อ
        return None
    return json.loads(raw.decode(ENCODING))  # แปลง bytes → JSON → dict แล้วส่งกลับ

# ══════════════════════════════════════════════
#   ฟังก์ชันจัดการ Client แต่ละคน
#   (ถูกเรียกใน Thread แยกต่างหากสำหรับแต่ละ Client)
# ══════════════════════════════════════════════
def handle_client(client_socket, client_addr):
    print(f"✅ Client เชื่อมต่อ → {client_addr[0]}:{client_addr[1]}")

    try:
        while True:                                    # วนลูปรับคำสั่งจาก Client ไปเรื่อยๆ
            data = receive_request(client_socket)      # รับข้อมูลจาก Client

            if data is None:                           # ถ้า Client ตัดการเชื่อมต่อ
                break                                  # ออกจากลูป

            action = data.get("action", "")            # ดึงคำสั่งจากข้อมูล
            print(f"📩 รับคำสั่ง '{action}' จาก {client_addr[0]}")

            # ── คำสั่ง ping: ทดสอบว่า Server ยังทำงานอยู่ ──
            if action == "ping":
                send_response(client_socket, {
                    "status":  "pong",
                    "message": "นำโชคพร้อมทำนายดวงแล้ว! 🐱"
                })

            # ── คำสั่ง fortune: ขอทำนายดวง ──
            elif action == "fortune":
                name      = data.get("name", "")
                birthdate = data.get("birthdate", "")
                category  = data.get("category", "")

                # ส่งไปตรวจสอบที่ validator.py ทีเดียวครบทุก field
                valid, errors = validate_all(name, birthdate, category)

                if not valid:                          # ถ้ามี field ไหนผิด
                    send_response(client_socket, {
                        "status": "error",
                        "errors": errors               # ส่ง dict ของ error แต่ละ field กลับไป
                    })
                    print(f"⚠️  ข้อมูลไม่ถูกต้อง: {errors}")
                else:                                  # ถ้าทุก field ผ่าน
                    print(f"🔮 ทำนายดวง: {name} | {birthdate} | {category}")
                    result = generate_fortune(name.strip(), birthdate.strip(), category.strip())
                    send_response(client_socket, result)   # ส่งผลดวงกลับ Client

            # ── คำสั่งไม่รู้จัก ──
            else:
                send_response(client_socket, {
                    "status":  "error",
                    "message": f"ไม่รู้จักคำสั่ง: '{action}'"
                })

    except ConnectionResetError:           # Client ปิดโปรแกรมกะทันหัน
        print(f"⚠️  Client {client_addr[0]} ตัดการเชื่อมต่อกะทันหัน")
    except json.JSONDecodeError:           # ได้รับข้อมูล JSON ผิดรูปแบบ
        print(f"⚠️  JSON ผิดรูปแบบจาก {client_addr[0]}")
    except Exception as e:                 # ข้อผิดพลาดอื่นๆ
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        client_socket.close()              # ปิด socket ของ Client คนนี้เสมอ
        print(f"🔌 Client ออกไปแล้ว → {client_addr[0]}:{client_addr[1]}\n")

# ══════════════════════════════════════════════
#   ฟังก์ชันหลัก: วนรับ Client เข้ามาเรื่อยๆ
# ══════════════════════════════════════════════
def run_server(server):
    while True:                                        # วนรอรับ Client ใหม่ไปเรื่อยๆ
        client_socket, client_addr = server.accept()   # หยุดรอจนมี Client เชื่อมต่อเข้ามา

        # สร้าง Thread ใหม่สำหรับ Client คนนี้โดยเฉพาะ
        # ทำให้ Client หลายคนใช้งานได้พร้อมกันโดยไม่รอคิว
        t = threading.Thread(
            target=handle_client,                      # ฟังก์ชันที่จะรันใน Thread นี้
            args=(client_socket, client_addr),         # ส่ง socket และ address เข้าไป
            daemon=True                                # Thread จบอัตโนมัติเมื่อโปรแกรมหลักจบ
        )
        t.start()                                      # เริ่มรัน Thread

# ══════════════════════════════════════════════
#   Main: จุดเริ่มต้นโปรแกรม
# ══════════════════════════════════════════════
def main():
    server = create_server()    # สร้าง Server Socket
    try:
        run_server(server)      # วนรับ Client ไปเรื่อยๆ
    except KeyboardInterrupt:   # กด Ctrl+C เพื่อหยุด
        print("\n🐱 กำลังปิด Server...")
    finally:
        server.close()          # ปิด Server Socket
        print("🔒 Server ปิดแล้ว")

main()                          # เรียกใช้งานโปรแกรม
