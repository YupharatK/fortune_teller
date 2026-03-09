import re                              # ใช้สำหรับตรวจสอบรูปแบบข้อความ (Regular Expression)
from datetime import datetime          # ใช้สำหรับตรวจสอบวันที่

# ══════════════════════════════════════════════
#   ค่าคงที่สำหรับการตรวจสอบ
# ══════════════════════════════════════════════
VALID_CATEGORIES  = ("love", "work", "money", "study")  # หมวดหมู่ที่รับได้
MIN_NAME_LENGTH   = 2                  # ความยาวชื่อขั้นต่ำ
MAX_NAME_LENGTH   = 50                 # ความยาวชื่อสูงสุด
MIN_BIRTH_YEAR    = 1900               # ปีเกิดเก่าสุดที่รับได้
MAX_BIRTH_YEAR    = datetime.now().year  # ปีเกิดล่าสุดที่รับได้ (ปีปัจจุบัน)

# ══════════════════════════════════════════════
#   ฟังก์ชันตรวจสอบชื่อ-นามสกุล
# ══════════════════════════════════════════════
def validate_name(name: str) -> tuple[bool, str]:
    """
    ตรวจสอบชื่อ-นามสกุล
    รับ  : name (str)
    คืนค่า: (True, "") ถ้าผ่าน
            (False, "ข้อความแจ้งเตือน") ถ้าไม่ผ่าน
    """
    name = name.strip()                # ตัดช่องว่างหน้า-หลังออก

    if not name:                       # ถ้าชื่อว่างเปล่า
        return False, "กรุณากรอกชื่อ-นามสกุล"

    if len(name) < MIN_NAME_LENGTH:    # ถ้าชื่อสั้นเกินไป
        return False, f"ชื่อ-นามสกุลต้องมีอย่างน้อย {MIN_NAME_LENGTH} ตัวอักษร"

    if len(name) > MAX_NAME_LENGTH:    # ถ้าชื่อยาวเกินไป
        return False, f"ชื่อ-นามสกุลต้องไม่เกิน {MAX_NAME_LENGTH} ตัวอักษร"

    # ตรวจว่ามีเฉพาะอักษรไทย, อักษรอังกฤษ, ช่องว่าง, จุด, ขีดกลาง เท่านั้น
    pattern = r'^[ก-๙a-zA-Z\s.\-]+$'
    if not re.match(pattern, name):
        return False, "ชื่อ-นามสกุลมีอักขระที่ไม่อนุญาต (ใช้ได้เฉพาะตัวอักษรไทย, อังกฤษ, ช่องว่าง)"

    if not any(c.isalpha() for c in name):  # ต้องมีตัวอักษรอย่างน้อย 1 ตัว
        return False, "ชื่อ-นามสกุลต้องมีตัวอักษรอย่างน้อย 1 ตัว"

    return True, ""                    # ผ่านทุกเงื่อนไข

# ══════════════════════════════════════════════
#   ฟังก์ชันตรวจสอบวันเดือนปีเกิด
# ══════════════════════════════════════════════
def validate_birthdate(birthdate: str) -> tuple[bool, str]:
    """
    ตรวจสอบวันเดือนปีเกิด รูปแบบ YYYY-MM-DD
    รับ  : birthdate (str)
    คืนค่า: (True, "") ถ้าผ่าน
            (False, "ข้อความแจ้งเตือน") ถ้าไม่ผ่าน
    """
    birthdate = birthdate.strip()      # ตัดช่องว่างออก

    if not birthdate:                  # ถ้าว่างเปล่า
        return False, "กรุณากรอกวันเดือนปีเกิด"

    # ตรวจรูปแบบว่าเป็น YYYY-MM-DD หรือไม่
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, birthdate):
        return False, "รูปแบบวันเกิดต้องเป็น YYYY-MM-DD (เช่น 2000-03-15)"

    # แยกปี เดือน วัน
    try:
        dt = datetime.strptime(birthdate, "%Y-%m-%d")  # แปลงเป็น datetime
    except ValueError:
        return False, "วันเดือนปีเกิดไม่ถูกต้อง (เช่น เดือนต้องเป็น 01-12)"

    # ตรวจปีว่าอยู่ในช่วงที่รับได้
    if dt.year < MIN_BIRTH_YEAR:
        return False, f"ปีเกิดต้องไม่น้อยกว่า {MIN_BIRTH_YEAR}"

    if dt.year > MAX_BIRTH_YEAR:
        return False, f"ปีเกิดต้องไม่เกินปีปัจจุบัน ({MAX_BIRTH_YEAR})"

    # ตรวจว่าวันเกิดไม่ใช่วันในอนาคต
    if dt.date() > datetime.now().date():
        return False, "วันเกิดต้องไม่เป็นวันในอนาคต"

    return True, ""                    # ผ่านทุกเงื่อนไข

# ══════════════════════════════════════════════
#   ฟังก์ชันตรวจสอบหมวดหมู่ดวง
# ══════════════════════════════════════════════
def validate_category(category: str) -> tuple[bool, str]:
    """
    ตรวจสอบหมวดหมู่ดวง
    รับ  : category (str) → "love" / "work" / "money" / "study"
    คืนค่า: (True, "") ถ้าผ่าน
            (False, "ข้อความแจ้งเตือน") ถ้าไม่ผ่าน
    """
    if not category:                   # ถ้าว่างเปล่า
        return False, "กรุณาเลือกหมวดหมู่ดวง"

    if category not in VALID_CATEGORIES:  # ถ้าไม่ใช่หมวดที่กำหนด
        return False, f"หมวดหมู่ไม่ถูกต้อง ต้องเป็น: {', '.join(VALID_CATEGORIES)}"

    return True, ""                    # ผ่านทุกเงื่อนไข

# ══════════════════════════════════════════════
#   ฟังก์ชันตรวจสอบทุกอย่างพร้อมกัน (รวม)
# ══════════════════════════════════════════════
def validate_all(name: str, birthdate: str, category: str) -> tuple[bool, dict]:
    """
    ตรวจสอบข้อมูลทั้งหมดในครั้งเดียว
    รับ  : name, birthdate, category
    คืนค่า: (True,  {}) ถ้าผ่านทั้งหมด
            (False, {"name": "...", "birthdate": "...", "category": "..."}) ถ้ามี error
    """
    errors = {}                        # dict เก็บข้อผิดพลาดของแต่ละ field

    ok, msg = validate_name(name)      # ตรวจชื่อ
    if not ok:
        errors["name"] = msg           # เก็บ error ของชื่อ

    ok, msg = validate_birthdate(birthdate)  # ตรวจวันเกิด
    if not ok:
        errors["birthdate"] = msg      # เก็บ error ของวันเกิด

    ok, msg = validate_category(category)    # ตรวจหมวดหมู่
    if not ok:
        errors["category"] = msg       # เก็บ error ของหมวดหมู่

    if errors:                         # ถ้ามี error อย่างน้อย 1 อย่าง
        return False, errors
    return True, {}                    # ผ่านทุก field

# ══════════════════════════════════════════════
#   ทดสอบ (รันไฟล์นี้โดยตรง)
# ══════════════════════════════════════════════
if __name__ == "__main__":

    print("=" * 50)
    print("  ทดสอบ validate_name()")
    print("=" * 50)
    test_names = [
        ("สมชาย ใจดี",   "✅ ปกติ"),
        ("",              "❌ ว่างเปล่า"),
        ("A",             "❌ สั้นเกิน"),
        ("John Doe",      "✅ ภาษาอังกฤษ"),
        ("1234",          "❌ ตัวเลขล้วน"),
        ("นภา@email",     "❌ มีอักขระพิเศษ"),
    ]
    for name, desc in test_names:
        ok, msg = validate_name(name)
        status = "ผ่าน ✅" if ok else f"ไม่ผ่าน ❌ → {msg}"
        print(f"  {desc:20s} | '{name:15s}' → {status}")

    print()
    print("=" * 50)
    print("  ทดสอบ validate_birthdate()")
    print("=" * 50)
    test_dates = [
        ("2000-08-15",  "✅ ปกติ"),
        ("",            "❌ ว่างเปล่า"),
        ("15/08/2000",  "❌ รูปแบบผิด"),
        ("2000-13-01",  "❌ เดือนผิด"),
        ("2000-02-30",  "❌ วันผิด"),
        ("1800-01-01",  "❌ ปีเก่าเกิน"),
        ("2099-01-01",  "❌ อนาคต"),
    ]
    for date, desc in test_dates:
        ok, msg = validate_birthdate(date)
        status = "ผ่าน ✅" if ok else f"ไม่ผ่าน ❌ → {msg}"
        print(f"  {desc:20s} | '{date:12s}' → {status}")

    print()
    print("=" * 50)
    print("  ทดสอบ validate_all()")
    print("=" * 50)
    ok, errors = validate_all("สมชาย ใจดี", "1995-08-15", "love")
    print(f"  ข้อมูลถูกต้องทั้งหมด → {'ผ่าน ✅' if ok else errors}")

    ok, errors = validate_all("", "1995-13-01", "unknown")
    print(f"  ข้อมูลผิดทั้งหมด     → ไม่ผ่าน ❌")
    for field, msg in errors.items():
        print(f"    • {field}: {msg}")
