
import asyncio
import json
import os
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8253189841:AAHOskmqauyFDffv_LKT3lt09-65xRQB0_Q"
USTOZ_IDS = [7008259110, 6022385042]    # Ustoz Telegram ID larini shu yerga yozing, masalan: [123456789]
DATA_FILE = "data.json"
# ======================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =================== MA'LUMOTLAR ===================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"lists": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_secret_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_student_id(used_ids):
    while True:
        id_num = random.randint(10, 999)
        id_str = str(id_num).zfill(3)
        if id_str not in used_ids:
            return id_str

def is_ustoz(user_id):
    return user_id in USTOZ_IDS

def get_last_list(uid):
    """Ustozning oxirgi yaratgan listini qaytaradi (code, list_data)"""
    data = load_data()
    my_lists = [(code, lst) for code, lst in data["lists"].items() if lst["owner_id"] == uid]
    if not my_lists:
        return None, None
    # Oxirgi element (JSON tartibida oxirgi)
    code, lst = my_lists[-1]
    return code, lst


# =================== HOLATLAR ===================
class UstozState(StatesGroup):
    list_name = State()
    confirm_clear = State()

class OquvchiState(StatesGroup):
    secret_code = State()
    full_name = State()


# =================== KLAVIATURALAR ===================
def ustoz_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Jańa dizim jaratıw")],
        [KeyboardButton(text="📁 Meniń dizimlerim")],
        [KeyboardButton(text="🗑 Hámmesin tazalaw")],
    ], resize_keyboard=True)

def oquvchi_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📝 Dizimnen ótiw")],
    ], resize_keyboard=True)

def confirm_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Awa, tazalaw"), KeyboardButton(text="❌ Joq, bıykarlaw")],
    ], resize_keyboard=True)


# =================== /START ===================
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    if is_ustoz(uid):
        code, lst = get_last_list(uid)
        if lst:
            await message.answer(
                f"👨‍🏫 Xosh keldińiz, Ustaz!\n\n"
                f"📋 Aktiv dizim :<b>{lst['name']}</b>\n"
                f"👥 Oqıwshılar sanı: <b>{len(lst['students'])}</b>\n\n"
                f"ID nomer jazsańız — oqıwshın Topaman! \nYamasa tómendegi sádeplerden paydalanıw:",
                parse_mode="HTML",
                reply_markup=ustoz_menu()
            )
        else:
            await message.answer(
                "👨‍🏫 Xosh keldińiz, Ustaz! \n\nEle dizim joq. Jańa dizim jaratıw:",
                reply_markup=ustoz_menu()
            )
    else:
        await message.answer(
            "👋 Xosh keldińiz! \n\nDizimnen ótiw ushın túyme basıń:",
            reply_markup=oquvchi_menu()
        )


# =================== USTOZ: YANGI RO'YXAT ===================
@dp.message(F.text == "📋 Jańa dizim jaratıw")
async def new_list_start(message: types.Message, state: FSMContext):
    if not is_ustoz(message.from_user.id):
        return
    await message.answer("📝 Dizim atınıń kirgiziń:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(UstozState.list_name)

@dp.message(UstozState.list_name)
async def new_list_name(message: types.Message, state: FSMContext):
    list_name = message.text.strip()
    secret_code = generate_secret_code()

    data = load_data()
    data["lists"][secret_code] = {
        "name": list_name,
        "owner_id": message.from_user.id,
        "students": {}
    }
    save_data(data)

    await state.clear()
    await message.answer(
        f"✅ Dizim tabıslı jaratıldı!\n\n"
        f"📋 Dizim atı: <b>{list_name}</b>\n"
        f"🔑 Jasırın kod: <code>{secret_code}</code>\n\n"
        f"Bul kodtı oqıwshılarǵa beriń!\n\n"
        f"Endi ID nomer jazıp oqıwshılardı qıdırıwıńız múmkin.",
        parse_mode="HTML",
        reply_markup=ustoz_menu()
    )


# =================== USTOZ: RO'YXATLARIM ===================
@dp.message(F.text == "📁 Meniń dizimlerim")
async def my_lists(message: types.Message):
    if not is_ustoz(message.from_user.id):
        return

    data = load_data()
    uid = message.from_user.id
    my = [(code, lst) for code, lst in data["lists"].items() if lst["owner_id"] == uid]

    if not my:
        await message.answer("📭 Sizde ele dizim joq.")
        return

    for code, lst in my:
        students = lst["students"]
        if not students:
            text = f"📋 <b>{lst['name']}</b>\n🔑 Kod: <code>{code}</code>\n\n👥 Oqıwshılar joq"
        else:
            lines = [f"📋 <b>{lst['name']}</b>\n🔑 Kod: <code>{code}</code>\n"]
            for i, (sid, sname) in enumerate(students.items(), 1):
                lines.append(f"{i}. {sname}  |  ID: <b>{sid}</b>")
            text = "\n".join(lines)

        await message.answer(text, parse_mode="HTML")


# =================== USTOZ: HAMMASINI TOZALASH ===================
@dp.message(F.text == "🗑 Hámmesin tazalaw")
async def clear_all_start(message: types.Message, state: FSMContext):
    if not is_ustoz(message.from_user.id):
        return
    await message.answer(
        "⚠️ <b>Dıqqat! </b>\n\nBarlıq dizimler hám oqıwshılar maǵlıwmatları óshiriledi. \n\nHaqıyqatn da tazalawdı qáleysizbe?",
        parse_mode="HTML",
        reply_markup=confirm_keyboard()
    )
    await state.set_state(UstozState.confirm_clear)

@dp.message(UstozState.confirm_clear, F.text == "✅ Awa, tazalaw")
async def clear_all_confirm(message: types.Message, state: FSMContext):
    save_data({"lists": {}})
    await state.clear()
    await message.answer(
        "✅ Barlıq maǵlıwmatlar tazalandı! Endi tazadan baslawıńız múmkin.",
        reply_markup=ustoz_menu()
    )

@dp.message(UstozState.confirm_clear, F.text == "❌ Yaq, bıykarlaw")
async def clear_all_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("↩️ Bıykar qilindi.", reply_markup=ustoz_menu())


# =================== USTOZ: ID ORQALI QIDIRISH (to'g'ridan to'g'ri) ===================
@dp.message(F.text.regexp(r'^\d{2,3}$'))
async def search_by_id_direct(message: types.Message, state: FSMContext):
    # Faqat ustoz uchun va hech qanday holat bo'lmaganda
    if not is_ustoz(message.from_user.id):
        return
    current_state = await state.get_state()
    if current_state is not None:
        return

    uid = message.from_user.id
    student_id = message.text.strip().zfill(3)

    code, lst = get_last_list(uid)

    if not lst:
        await message.answer("❌ Sizde ele aktiv dizim joq. Aldın dizim jaratıw.")
        return

    students = lst["students"]

    if student_id in students:
        name = students[student_id]
        place = list(students.keys()).index(student_id) + 1
        await message.answer(
            f"✅ Tabıldı!\n\n"
            f"📋 Dizim: <b>{lst['name']}</b>\n"
            f"📌 Orın: <b>{place}</b>\n"
            f"👤 Atı: <b>{name}</b>\n"
            f"🆔 ID: <b>{student_id}</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ ID: <b>{student_id}</b> - Cifrlı oqıwshı tabılmadı.\n"
            f"📋 Aktiv dizim: <b>{lst['name']}</b>",
            parse_mode="HTML"
        )


# =================== O'QUVCHI: RO'YXATDAN O'TISH ===================
@dp.message(F.text == "📝 Dizimnen ótiw")
async def register_start(message: types.Message, state: FSMContext):
    if is_ustoz(message.from_user.id):
        return
    await message.answer("🔑 Jasırın kodtı kirgiziń:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OquvchiState.secret_code)

@dp.message(OquvchiState.secret_code)
async def register_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    data = load_data()

    if code not in data["lists"]:
        await message.answer("❌ Nadurıs kod yamasa dizim óshirilgen! Qayta kirgiziń:")
        return

    await state.update_data(reg_code=code)
    await message.answer(
        "✅ Jasırın kod tabıslı!\n\n"
        "👤 At hám familiyańızdı kirgiziń:\n"
        "Masalan: <i>Altınbaev Mıńbay</i>",
        parse_mode="HTML"
    )
    await state.set_state(OquvchiState.full_name)

@dp.message(OquvchiState.full_name)
async def register_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()

    if len(full_name.split()) < 2:
        await message.answer(
            "❗ Iltimas, at hám famılıyanı tolıq kirgiziń\nMısalı: <i>Altınbaev Mıńbay</i>:",
            parse_mode="HTML"
        )
        return

    fsm_data = await state.get_data()
    code = fsm_data.get("reg_code")

    data = load_data()

    # Ro'yxat hali mavjudmi tekshirish
    if code not in data["lists"]:
        await state.clear()
        await message.answer(
            "❌ Bu dizim óshirilgen! Ustoz bilan bog'lanıń.",
            reply_markup=oquvchi_menu()
        )
        return

    lst = data["lists"][code]
    students = lst["students"]

    if full_name in students.values():
        await state.clear()
        await message.answer(
            "⚠️ Siz álleqashan bul dizimde dizimnen ótkensiz!",
            reply_markup=oquvchi_menu()
        )
        return

    student_id = generate_student_id(set(students.keys()))
    students[student_id] = full_name
    place = len(students)

    save_data(data)
    await state.clear()

    await message.answer(
        f"🎉 Qabıllandı!\n\n"
        f"📌 {place}. {full_name}\n"
        f"🆔 ID nomerıńız: <b>{student_id}</b>\n\n"
        f"⚠️ Usi ID nomerıńızdi eslep qalıń!",
        parse_mode="HTML",
        reply_markup=oquvchi_menu()
    )


# =================== ISHGA TUSHIRISH ===================
async def main():
    print("✅ Bot iske tusti...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())