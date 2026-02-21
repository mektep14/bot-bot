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
USTOZ_IDS = [7008259110, 6022385042]
DATA_FILE = "data.json"
NARX = "10.000"
# ======================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =================== MA'LUMOTLAR ===================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"lists": {}, "click_info": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "click_info" not in data:
        data["click_info"] = {}
    return data

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
    data = load_data()
    my_lists = [(code, lst) for code, lst in data["lists"].items() if lst["owner_id"] == uid]
    if not my_lists:
        return None, None
    return my_lists[-1]

def get_name(info):
    return info["name"] if isinstance(info, dict) else info

def get_pay(info):
    if isinstance(info, dict):
        pay = info.get("pay", "")
        return "💳 Click" if pay == "click" else "💵 Naq" if pay == "naxt" else "❓"
    return "❓"

def format_list(lst_name, code, students):
    lines = [
        f"📋 {lst_name}\n",
        f"🔑 Kod: {code}\n",
    ]
    if not students:
        lines.append("\n👥 Oqıwshılar joq")
    else:
        lines.append("")
        for i, (sid, info) in enumerate(students.items(), 1):
            name = get_name(info)
            pay = get_pay(info)
            lines.append(f"{i}. {name}  |  ID: {sid}  |  Tolem: {pay}")
        lines.append(f"\n👥 Jámi: {len(students)} oqıwshı")
    return "\n".join(lines)


# =================== HOLATLAR ===================
class UstozState(StatesGroup):
    list_name = State()
    confirm_clear = State()
    click_ism = State()
    click_raqam = State()
    click_username = State()
    edit_action = State()
    edit_select = State()
    edit_new_name = State()
    add_name = State()

class OquvchiState(StatesGroup):
    secret_code = State()
    full_name = State()
    payment_choice = State()


# =================== KLAVIATURALAR ===================
def ustoz_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Jańa dizim jaratıw")],
        [KeyboardButton(text="📁 Meniń dizimlerim")],
        [KeyboardButton(text="✏️ Dizimge ózgertiwler kiritw")],
        [KeyboardButton(text="💳 Click maǵlıwmatların sozlaw")],
        [KeyboardButton(text="🗑 Hámmesin tazalaw")],
    ], resize_keyboard=True)

def oquvchi_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📝 Dizimnen ótiw")],
    ], resize_keyboard=True)

def confirm_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Awa, tazalaw"), KeyboardButton(text="❌ Yaq, bıykarlaw")],
    ], resize_keyboard=True)

def payment_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💳 Click"), KeyboardButton(text="💵 Naq")],
    ], resize_keyboard=True)

def edit_action_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🗑 Oshiriw"), KeyboardButton(text="✏️ Ozgertiw")],
        [KeyboardButton(text="➕ Jańa oqıwshı qosıw")],
        [KeyboardButton(text="↩️ Arqaga")],
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
                f"📋 Aktiv dizim: <b>{lst['name']}</b>\n"
                f"👥 Oqıwshılar sanı: <b>{len(lst['students'])}</b>\n\n"
                f"ID nomer jazsańız — oqıwshın tabaman!\n"
                f"Yamasa tómendegi túymelerden paydalanıń:",
                parse_mode="HTML",
                reply_markup=ustoz_menu()
            )
        else:
            await message.answer(
                "👨‍🏫 Xosh keldińiz, Ustaz!\n\nEle dizim joq. Jańa dizim jaratıń:",
                reply_markup=ustoz_menu()
            )
    else:
        await message.answer(
            "👋 Xosh keldińiz!\n\nDizimnen ótiw ushın túyme basıń:",
            reply_markup=oquvchi_menu()
        )


# =================== USTOZ: YANGI RO'YXAT ===================
@dp.message(F.text == "📋 Jańa dizim jaratıw")
async def new_list_start(message: types.Message, state: FSMContext):
    if not is_ustoz(message.from_user.id):
        return
    await message.answer("📝 Dizim atın kirgiziń:", reply_markup=ReplyKeyboardRemove())
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
        f"Bul kodtı oqıwshılarǵa beriń!",
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
        text = format_list(lst["name"], code, lst["students"])
        await message.answer(text)


# =================== USTOZ: CLICK SOZLASH ===================
@dp.message(F.text == "💳 Click maǵlıwmatların sozlaw")
async def click_setup_start(message: types.Message, state: FSMContext):
    if not is_ustoz(message.from_user.id):
        return
    await message.answer(
        "👤 Click kártası iyesiniń atın kirgiziń:\n(Mısalı: <code>Altınbaev Mıńbay</code>)",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(UstozState.click_ism)

@dp.message(UstozState.click_ism)
async def click_setup_ism(message: types.Message, state: FSMContext):
    await state.update_data(click_ism=message.text.strip())
    await message.answer(
        "📱 Click kártası sanıń kirgiziń:\n(Mısalı: <code>9901234567</code>)",
        parse_mode="HTML"
    )
    await state.set_state(UstozState.click_raqam)

@dp.message(UstozState.click_raqam)
async def click_setup_raqam(message: types.Message, state: FSMContext):
    await state.update_data(click_raqam=message.text.strip())
    await message.answer(
        "💬 Telegram username'iń kirgiziń:\n(Mısalı: <code>@ustoz_click</code>)",
        parse_mode="HTML"
    )
    await state.set_state(UstozState.click_username)

@dp.message(UstozState.click_username)
async def click_setup_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username
    fsm_data = await state.get_data()
    ism = fsm_data.get("click_ism")
    raqam = fsm_data.get("click_raqam")
    data = load_data()
    data["click_info"][str(message.from_user.id)] = {"ism": ism, "raqam": raqam, "username": username}
    save_data(data)
    await state.clear()
    await message.answer(
        f"✅ Click maǵlıwmatları saqlandı!\n\n"
        f"👤 Kárta iyesi: <b>{ism}</b>\n"
        f"📱 Nomer: <b>{raqam}</b>\n"
        f"💬 Username: <b>{username}</b>",
        parse_mode="HTML",
        reply_markup=ustoz_menu()
    )


# =================== USTOZ: O'ZGARTIRISH ===================
@dp.message(F.text == "✏️ Dizimge ózgertiwler kiritw")
async def edit_list_start(message: types.Message, state: FSMContext):
    if not is_ustoz(message.from_user.id):
        return
    uid = message.from_user.id
    code, lst = get_last_list(uid)
    if not lst:
        await message.answer("❌ Sizde ele aktiv dizim joq.")
        return
    students = lst["students"]
    if not students:
        await message.answer(
            f"📋 {lst['name']}\n\n👥 Ele oqıwshı joq. ",
            reply_markup=edit_action_keyboard()
        )
    else:
        lines = [
            f"📋 {lst['name']}",
            f"🔑 Kod: {code}",
            f"",
            f"Ózgertiw ushın ID jazıń:\n",
        ]
        for i, (sid, info) in enumerate(students.items(), 1):
            name = get_name(info)
            pay = get_pay(info)
            lines.append(f"{i}. {name}  |  ID: {sid}  |  Tolem: {pay}")
        await message.answer("\n".join(lines), reply_markup=edit_action_keyboard())
    await state.update_data(edit_code=code)
    await state.set_state(UstozState.edit_action)


@dp.message(UstozState.edit_action)
async def edit_action_handler(message: types.Message, state: FSMContext):
    import re
    text = message.text.strip()
    fsm_data = await state.get_data()
    code = fsm_data.get("edit_code")
    data = load_data()
    students = data["lists"][code]["students"]

    if text == "↩️ Arqaga":
        await state.clear()
        await message.answer("Menyu:", reply_markup=ustoz_menu())
        return

    if text == "➕ Jańa oqıwshı qosıw":
        await message.answer(
            "👤 Jańa oqıwshınıń at familiyasın kirgiziń: \nMısalı: Palenshiyev Talenshe",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(UstozState.add_name)
        return

    if re.match(r'^\d{2,3}$', text):
        student_id = text.zfill(3)
        if student_id not in students:
            await message.answer(f"❌ ID: {student_id} tabiladi.")
            return
        info = students[student_id]
        name = get_name(info)
        pay = get_pay(info)
        await state.update_data(selected_id=student_id)
        await message.answer(
            f"Tańlandı:\n{name}  |  ID: {student_id}  |  {pay}\n\nNe qılmaqshısız?",
            reply_markup=ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="🗑 Oshiriw"), KeyboardButton(text="✏️ Ozgertiw")],
                [KeyboardButton(text="↩️ Arqaga")],
            ], resize_keyboard=True)
        )
        await state.set_state(UstozState.edit_select)
        return

    await message.answer("❗ ID nomer jazıń yamasa tuyme saylań.")


@dp.message(UstozState.edit_select)
async def edit_select_handler(message: types.Message, state: FSMContext):
    text = message.text.strip()
    fsm_data = await state.get_data()
    code = fsm_data.get("edit_code")
    student_id = fsm_data.get("selected_id")
    data = load_data()
    students = data["lists"][code]["students"]

    if text == "↩️ Arqaga":
        await state.clear()
        await edit_list_start(message, state)
        return

    if text == "🗑 Oshiriw":
        info = students.pop(student_id)
        name = get_name(info)
        save_data(data)
        await state.clear()
        await message.answer(
            f"✅ Oshirildi!\n{name}  |  ID: {student_id}",
            reply_markup=ustoz_menu()
        )
        return

    if text == "✏️ Ozgertiw":
        info = students[student_id]
        name = get_name(info)
        await message.answer(
            f"✏️ Jańa at famılıyanı kirgiziń: \n ( Házirgi: {name})",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(UstozState.edit_new_name)
        return


@dp.message(UstozState.edit_new_name)
async def edit_new_name_handler(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if len(new_name.split()) < 2:
        await message.answer("❗ Iltimas, at hám famılıyanı tolıq kirgiziń:")
        return
    fsm_data = await state.get_data()
    code = fsm_data.get("edit_code")
    student_id = fsm_data.get("selected_id")
    data = load_data()
    info = data["lists"][code]["students"][student_id]
    old_name = get_name(info)
    if isinstance(info, dict):
        data["lists"][code]["students"][student_id]["name"] = new_name
    else:
        data["lists"][code]["students"][student_id] = {"name": new_name, "pay": "naxt"}
    save_data(data)
    await state.clear()
    await message.answer(
        f"✅ Ozgertildi!\n{old_name} → {new_name}\nID: {student_id}",
        reply_markup=ustoz_menu()
    )


@dp.message(UstozState.add_name)
async def add_student_handler(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer("❗ Iltimas, at hám famılıyanı tolıq kirgiziń:")
        return
    fsm_data = await state.get_data()
    code = fsm_data.get("edit_code")
    data = load_data()
    students = data["lists"][code]["students"]
    for info in students.values():
        if get_name(info) == full_name:
            await message.answer("⚠️ Bul at álleqashan dizimde bar!")
            return
    student_id = generate_student_id(set(students.keys()))
    students[student_id] = {"name": full_name, "pay": "naxt"}
    place = len(students)
    save_data(data)
    await state.clear()
    await message.answer(
        f"✅ Qosıldı!\n{place}. {full_name}  |  ID: {student_id}  |  Tolem: 💵 Naq",
        reply_markup=ustoz_menu()
    )


# =================== USTOZ: TOZALASH ===================
@dp.message(F.text == "🗑 Hámmesin tazalaw")
async def clear_all_start(message: types.Message, state: FSMContext):
    if not is_ustoz(message.from_user.id):
        return
    await message.answer(
        "⚠️ Barlıq dizimler hám oqıwshılar maǵlıwmatları óshiriledi.\n\nHaqıyqatn da tazalawdı qáleysizbe?",
        reply_markup=confirm_keyboard()
    )
    await state.set_state(UstozState.confirm_clear)

@dp.message(UstozState.confirm_clear, F.text == "✅ Awa, tazalaw")
async def clear_all_confirm(message: types.Message, state: FSMContext):
    data = load_data()
    data["lists"] = {}
    save_data(data)
    await state.clear()
    await message.answer("✅ Barlıq maǵlıwmatlar tazalandı!", reply_markup=ustoz_menu())

@dp.message(UstozState.confirm_clear, F.text == "❌ Yaq, bıykarlaw")
async def clear_all_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("↩️ Bıykar qilindi.", reply_markup=ustoz_menu())


# =================== USTOZ: ID ORQALI QIDIRISH ===================
@dp.message(F.text.regexp(r'^\d{2,3}$'))
async def search_by_id_direct(message: types.Message, state: FSMContext):
    if not is_ustoz(message.from_user.id):
        return
    current_state = await state.get_state()
    if current_state is not None:
        return
    uid = message.from_user.id
    student_id = message.text.strip().zfill(3)
    code, lst = get_last_list(uid)
    if not lst:
        await message.answer("❌ Sizde ele aktiv dizim joq.")
        return
    students = lst["students"]
    if student_id in students:
        info = students[student_id]
        name = get_name(info)
        pay = get_pay(info)
        place = list(students.keys()).index(student_id) + 1
        await message.answer(
            f"✅ Tabıldı!\n\n"
            f"📋 {lst['name']}\n"
            f"{place}. {name}  |  ID: {student_id}  |  To'lov: {pay}"
        )
    else:
        await message.answer(
            f"❌ ID: {student_id} tabiladi.\n"
            f"📋 Aktiv dizim: {lst['name']}"
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
        "Mısalı: Altınbaev Mıńbay"
    )
    await state.set_state(OquvchiState.full_name)

@dp.message(OquvchiState.full_name)
async def register_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer("❗ At hám famılıyanı tolıq kirgiziń.\nMısalı: Altınbaev Mıńbay")
        return
    fsm_data = await state.get_data()
    code = fsm_data.get("reg_code")
    data = load_data()
    if code not in data["lists"]:
        await state.clear()
        await message.answer("❌ Bul dızim óshirilgen! Ustaz benen baylanısıń.", reply_markup=oquvchi_menu())
        return
    students = data["lists"][code]["students"]
    for info in students.values():
        if get_name(info) == full_name:
            await state.clear()
            await message.answer("⚠️ Siz álleqashan dizimnen ótkensiz!", reply_markup=oquvchi_menu())
            return
    await state.update_data(reg_name=full_name)
    await message.answer(
        f"💰 Tólew summası: {NARX} swm\n\nQanday usılda tolemekshisiz?",
        reply_markup=payment_keyboard()
    )
    await state.set_state(OquvchiState.payment_choice)


@dp.message(OquvchiState.payment_choice)
async def payment_choice_handler(message: types.Message, state: FSMContext):
    choice = message.text.strip()
    if choice not in ["💳 Click", "💵 Naq"]:
        await message.answer("❗ Iltimas, tuymeden birin saylań!", reply_markup=payment_keyboard())
        return
    fsm_data = await state.get_data()
    code = fsm_data.get("reg_code")
    full_name = fsm_data.get("reg_name")
    data = load_data()
    if code not in data["lists"]:
        await state.clear()
        await message.answer("❌ Bul dızim óshirilgen!", reply_markup=oquvchi_menu())
        return
    students = data["lists"][code]["students"]
    student_id = generate_student_id(set(students.keys()))
    pay_type = "click" if choice == "💳 Click" else "naxt"
    students[student_id] = {"name": full_name, "pay": pay_type}
    place = len(students)
    save_data(data)
    await state.clear()

    if choice == "💵 Naq":
        await message.answer(
            f"✅ Siz tolıq dizimnen óttińiz!\n\n"
            f"{place}. {full_name}\n"
            f"🆔 ID: {student_id}  |  Tolem: 💵 Naq\n\n"
            f"💵 Test kúni pulińizdi alıp keliń!\n\n"
            f"⚠️ ID nomerıńızdi eslep qalıń!",
            reply_markup=oquvchi_menu()
        )
    else:
        owner_id = data["lists"][code]["owner_id"]
        click_info = data.get("click_info", {}).get(str(owner_id))
        if click_info:
            click_text = (
                f"💳 Click arqalı tólew:\n"
                f"👤 Kárta iyesi: {click_info.get('ism', '')}\n"
                f"📱 Nomer: {click_info['raqam']}\n"
                f"💬 Ustaz: {click_info['username']}\n\n"
                f"✅ Tólewdi ámelge asırıp, chek screenshotın ustazǵa jiberiń!"
            )
        else:
            click_text = "💳 Click maǵlıwmatları sazlanbaǵan. Ustaz benen baylanısıń."
        await message.answer(
            f"✅ Siz tolıq dizimnen óttińiz!\n\n"
            f"{place}. {full_name}\n"
            f"🆔 ID: {student_id}  |  Tolem: 💳 Click\n\n"
            f"{click_text}\n\n"
            f"⚠️ ID nomerıńızdi eslep qalıń!",
            reply_markup=oquvchi_menu()
        )


# =================== ISHGA TUSHIRISH ===================
async def main():
    print("✅ Bot iske tusti...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
