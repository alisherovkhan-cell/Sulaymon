import os
import re
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8747499724:AAHRYeqEDgOquPxceBgIJkeD2NeFoiSTsUE"
ADMIN_ID = 8597455078
ADMIN_USER = "@DlKTATOR_UZ"

# Kanallar ro'yxati
CHANNELS = [
    {"username": "@sulaymonnftbattle", "type": "public"},
    {"username": "@battler_go_uz", "type": "public"},
    {"username": "@battle_stars_go", "type": "public"},
    {"username": "@K0NKURS_UZ", "type": "public"}
]

IMAGE_URL = "https://picsum.photos/800/600"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar bazasi modeli
db_users = {}

class RegistrationState(StatesGroup):
    waiting_for_phone = State()

class AdminState(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_balance_user_id = State()
    waiting_for_balance_amount = State()
    waiting_for_support_reply = State()

class SupportState(StatesGroup):
    waiting_for_message = State()

def get_main_keyboard(user_id):
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🙋‍♂️ Stars Ishlash"))
    builder.row(KeyboardButton(text="📊 Hisobim"), KeyboardButton(text="💫 Stars Yechish"))
    builder.row(KeyboardButton(text="📝 Isbotlar kanal"))
    builder.row(KeyboardButton(text="🔎 Yordam"), KeyboardButton(text="📜 Qo'llanma"))
    if user_id == ADMIN_ID:
        builder.row(KeyboardButton(text="🛠 Admin paneli"))
    return builder.as_markup(resize_keyboard=True)

async def check_subscriptions(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel["username"], user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            pass
    return True

def get_channels_keyboard():
    builder = InlineKeyboardBuilder()
    for i, ch in enumerate(CHANNELS, start=1):
        link = f"https://t.me/{ch['username'][1:]}"
        builder.row(InlineKeyboardButton(text=f"{i}-kanalga a'zo bo'lish", url=link))
    builder.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs"))
    return builder.as_markup()

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split()
    referrer = None
    if len(args) > 1 and args[1].isdigit():
        referrer = int(args[1])
        if referrer == user_id:
            referrer = None

    if user_id not in db_users:
        db_users[user_id] = {
            "phone": None, "referrer": referrer, "stars": 0, "total_referred": 0,
            "withdrawn": 0, "registered": False, "name": message.from_user.full_name,
            "username": message.from_user.username or "Foydalanuvchi"
        }

    if not db_users[user_id]["registered"]:
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True))
        await message.answer(
            "Xush kelibsiz! Botdan foydalanish uchun faqat O'zbekiston raqamlari orqali ro'yxatdan o'tishingiz mumkin.\n"
            "Iltimos, pastdagi tugmani bosib telefon raqamingizni yuboring:",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        await state.set_state(RegistrationState.waiting_for_phone)
    else:
        if await check_subscriptions(user_id):
            await message.answer("Xush kelibsiz! Asosiy menyu:", reply_markup=get_main_keyboard(user_id))
        else:
            await message.answer("Botdan foydalanish uchun majburiy kanallarga (shaxsiy kanalga zayafka yuborish orqali) a'zo bo'lishingiz kerak:", reply_markup=get_channels_keyboard())

@dp.message(RegistrationState.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    if not phone.startswith('+'): phone = '+' + phone
    if not (phone.startswith('+998') or phone.startswith('998')):
        await message.answer("Kechirasiz, faqat O'zbekiston raqamlari (+998) orqali ro'yxatdan o'tish mumkin.")
        return

    db_users[user_id]["phone"] = phone
    db_users[user_id]["registered"] = True
    await state.clear()

    ref_id = db_users[user_id]["referrer"]
    if ref_id and ref_id in db_users:
        db_users[ref_id]["stars"] += 2
        db_users[ref_id]["total_referred"] += 1
        try: await bot.send_message(ref_id, "🎉 Taklif havolangiz orqali yangi foydalanuvchi ro'yxatdan o'tdi! Hisobingizga 2 ⭐️ qo'shildi.")
        except: pass

    if await check_subscriptions(user_id):
        await message.answer("Muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=get_main_keyboard(user_id))
    else:
        await message.answer("Botdan foydalanish uchun majburiy kanallarga a'zo bo'ling:", reply_markup=get_channels_keyboard())

@dp.callback_query(F.data == "check_subs")
async def check_subs_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in db_users or not db_users[user_id]["registered"]:
        await callback.answer("Avval ro'yxatdan o'ting!", show_alert=True)
        return
    if await check_subscriptions(user_id):
        await callback.message.delete()
        await callback.message.answer("Tabriklaymiz, barcha shartlarni bajardingiz!", reply_markup=get_main_keyboard(user_id))
    else:
        await callback.answer("Hamma kanallarga obuna bo'lishingiz yoki zayafka yuborgan bo'lishingiz shart!", show_alert=True)

@dp.message(F.text == "🙋‍♂️ Stars Ishlash")
async def stars_earn(message: types.Message):
    user_id = message.from_user.id
    if user_id not in db_users or not await check_subscriptions(user_id): return
    bot_user = await bot.get_me()
    ref_link = f"https://t.me/{bot_user.username}?start={user_id}"
    text = f"🔗 <b>{message.from_user.full_name}</b> Sizning taklif havolangiz:\n\n{ref_link}\n\n👆 Yuqoridagi taklif havolangizni do'stlaringizga tarqating va har bir to'liq ro'yxatdan o'tgan taklifingiz uchun 2 ⭐️ hisobingizga qo'shiladi."
    share_builder = InlineKeyboardBuilder()
    share_builder.row(InlineKeyboardButton(text="🚀 Ulashish", url=f"https://t.me/share/url?url={ref_link}"))
    try: await message.answer_photo(photo=IMAGE_URL, caption=text, parse_mode="HTML", reply_markup=share_builder.as_markup())
    except: await message.answer(text, parse_mode="HTML", reply_markup=share_builder.as_markup())

@dp.message(F.text == "📊 Hisobim")
async def my_account(message: types.Message):
    user_id = message.from_user.id
    if user_id not in db_users or not await check_subscriptions(user_id): return
    u = db_users[user_id]
    text = f"👤 Sizning ID raqamingiz: <code>{user_id}</code>\n\n🤑 Asosiy balansingiz: {u['stars']} ⭐️\n🥳 Takliflaringiz soni: {u['total_referred']} ta\n\n✳️ Yechib olgan Starslaringiz: {u['withdrawn']} ⭐️"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💫 Stars Yechish", callback_data="withdraw_stars"))
    await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())

@dp.message(F.text == "💫 Stars Yechish")
@dp.callback_query(F.data == "withdraw_stars")
async def withdraw_menu(event):
    message = event if isinstance(event, types.Message) else event.message
    text = "👇 Quyidagi to'lov tizimlaridan birini tanlang:"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="15 🧸", callback_data="gift_15"), InlineKeyboardButton(text="25 🎁", callback_data="gift_25"))
    builder.row(InlineKeyboardButton(text="50 🎁", callback_data="gift_50"), InlineKeyboardButton(text="100 💍", callback_data="gift_100"))
    if isinstance(event, types.CallbackQuery): await event.answer()
    await message.answer(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("gift_"))
async def process_gift_request(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    amount = int(callback.data.split("_")[1])
    if db_users[user_id]["stars"] < amount:
        await callback.answer(f"❌ Balansingizda yetarli mablag' mavjud emas! {amount} ⭐️ kerak.", show_alert=True)
        return
    await callback.answer("So'rov adminga yuborildi!", show_alert=True)
    admin_builder = InlineKeyboardBuilder()
    admin_builder.row(InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{user_id}_{amount}"), InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}_{amount}"))
    await bot.send_message(chat_id=ADMIN_ID, text=f"🚀 <b>Yangi so'rov!</b>\n\n👤 Foydalanuvchi: {db_users[user_id]['name']} (ID: {user_id})\n📞 Telefon: {db_users[user_id]['phone']}\n💰 Miqdor: {amount} ⭐️", parse_mode="HTML", reply_markup=admin_builder.as_markup())

@dp.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    parts = callback.data.split("_")
    target_user_id, amount = int(parts[1]), int(parts[2])
    if target_user_id in db_users and db_users[target_user_id]["stars"] >= amount:
        db_users[target_user_id]["stars"] -= amount
        db_users[target_user_id]["withdrawn"] += amount
        try: await bot.send_message(target_user_id, f"🎉 To'lovingiz tasdiqlandi! {amount} ⭐️ yechildi.")
        except: pass
        await callback.message.edit_text(f"✅ ID {target_user_id} uchun {amount} ⭐️ to'lov tasdiqlandi.")
    else: await callback.message.edit_text("❌ Foydalanuvchi topilmadi yoki balansi yetarsiz.")

@dp.callback_query(F.data.startswith("reject_"))
async def admin_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    parts = callback.data.split("_")
    target_user_id, amount = int(parts[1]), int(parts[2])
    try: await bot.send_message(target_user_id, f"❌ Sizning {amount} ⭐️ yechish so'rovingiz rad etildi.")
    except: pass
    await callback.message.edit_text(f"❌ ID {target_user_id} so'rovi rad etildi.")

@dp.message(F.text == "📝 Isbotlar kanal")
async def proofs_channel(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➡️ Kanalga o'tish", url="https://t.me/sulaymon_gifts_tolovlar"))
    await message.answer("Quyidagi kanal orqali to'lovlarni kuzatib boring:", reply_markup=builder.as_markup())

@dp.message(F.text == "🔎 Yordam")
async def help_cmd(message: types.Message, state: FSMContext):
    await message.answer("📝 Murojaat matnini yuboring:")
    await state.set_state(SupportState.waiting_for_message)

@dp.message(SupportState.waiting_for_message)
async def support_msg_received(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    admin_builder = InlineKeyboardBuilder()
    admin_builder.row(InlineKeyboardButton(text="✍️ Javob berish", callback_data=f"reply_{user_id}"))
    await bot.send_message(chat_id=ADMIN_ID, text=f"✉️ <b>Yangi murojaat!</b>\n\n🆔 ID: {user_id}\n📝 Matn: {message.text}", parse_mode="HTML", reply_markup=admin_builder.as_markup())
    await message.answer("Murojaatingiz yuborildi. Tez orada javob olasiz!")
    await state.clear()

@dp.callback_query(F.data.startswith("reply_"))
async def admin_reply_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await state.update_data(reply_target_id=int(callback.data.split("_")[1]))
    await callback.message.answer("Javob matnini yozing:")
    await state.set_state(AdminState.waiting_for_support_reply)

@dp.message(AdminState.waiting_for_support_reply)
async def admin_send_reply(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    try:
        await bot.send_message(data.get("reply_target_id"), f"✉️ <b>Admindan javob:</b>\n\n{message.text}", parse_mode="HTML")
        await message.answer("Javob yetkazildi.")
    except: await message.answer("Xatolik yuz berdi.")
    await state.clear()

@dp.message(F.text == "📜 Qo'llanma")
async def guide_cmd(message: types.Message):
    await message.answer("<b>Bot qoidalari 📜</b>\n\n🛑 Chaqirgan doʻstingiz kanallardan chiqib ketmasligi kerak.\n🚫 Multi-account taqiqlanadi.", parse_mode="HTML")

@dp.message(F.text == "🛠 Admin paneli")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"))
    builder.row(InlineKeyboardButton(text="💳 Balans boshqarish", callback_data="admin_balance"))
    builder.row(InlineKeyboardButton(text="📥 Hammaga xabar", callback_data="admin_broadcast"))
    await message.answer("🛠 Admin paneliga xush kelibsiz:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "admin_stats")
async def admin_stats_cb(callback: types.CallbackQuery):
    total = len(db_users)
    reg = sum(1 for u in db_users.values() if u.get("registered"))
    await callback.message.answer(f"📊 Statistika:\n\n👥 Umumiy: {total}\n✅ Ro'yxatdan o'tganlar: {reg}")

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_cb(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("📥 Xabar matnini kiriting:")
    await state.set_state(AdminState.waiting_for_broadcast)

@dp.message(AdminState.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Yuborilmoqda...")
    count = 0
    for uid in list(db_users.keys()):
        try:
            await bot.send_message(uid, message.text)
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"✅ Xabar {count} kishiga yuborildi.")

@dp.callback_query(F.data == "admin_balance")
async def admin_balance_cb(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Foydalanuvchi ID raqamini kiriting:")
    await state.set_state(AdminState.waiting_for_balance_user_id)

@dp.message(AdminState.waiting_for_balance_user_id)
async def process_balance_uid(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    target_id = int(message.text)
    if target_id not in db_users:
        db_users[target_id] = {"phone": None, "referrer": None, "stars": 0, "total_referred": 0, "withdrawn": 0, "registered": False, "name": "Noma'lum"}
    await state.update_data(target_uid=target_id)
    await message.answer("Miqdorni kiriting (masalan: 10 yoki -5):")
    await state.set_state(AdminState.waiting_for_balance_amount)

@dp.message(AdminState.waiting_for_balance_amount)
async def process_balance_amount(message: types.Message, state: FSMContext):
    try: amount = int(message.text)
    except: return
    data = await state.get_data()
    tid = data.get("target_uid")
    await state.clear()
    db_users[tid]["stars"] += amount
    await message.answer(f"✅ ID {tid} balansi o'zgartirildi. Hozirgi balans: {db_users[tid]['stars']} ⭐️")
    try: await bot.send_message(tid, f"🛠 Admin hisobingizni o'zgartirdi: {amount} ⭐️")
    except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
