import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "7933627272:AAEFM5erZHJswGZd_9wJjuOUUoPWZL_rDV0"
ADMIN_ID = 7314641258

# ==================== HOLATLAR ====================
TAOM_NOMI, TAOM_NARX, TAOM_RASM = range(3)
ICHIMLIK_NOMI, ICHIMLIK_NARX, ICHIMLIK_RASM = range(3, 6)
REKLAMA_MATNI = 6

# ==================== MA'LUMOTLAR (xotira) ====================
milliy_taomlar = []
turk_taomlar = []
ichimliklar = []
foydalanuvchilar = set()

# ==================== LOGGING (minimal - tezlik uchun) ====================
logging.basicConfig(level=logging.WARNING)  # INFO -> WARNING (log chiqarish kamaytirish)
logger = logging.getLogger(__name__)


# ==================== YORDAMCHI ====================
def asosiy_klaviatura():
    keyboard = [
        [KeyboardButton("🍽 Milliy taomlar"), KeyboardButton("🥙 Turk taomlar")],
        [KeyboardButton("🥤 Ichimliklar")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_klaviatura():
    keyboard = [
        [KeyboardButton("➕ Milliy taom qo'shish"), KeyboardButton("➕ Turk taom qo'shish")],
        [KeyboardButton("➕ Ichimlik qo'shish")],
        [KeyboardButton("❌ Taom o'chirish"), KeyboardButton("❌ Ichimlik o'chirish")],
        [KeyboardButton("📢 Reklama yuborish"), KeyboardButton("📊 Statistika")],
        [KeyboardButton("🏠 Asosiy menyu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def is_admin(user_id):
    return user_id == ADMIN_ID


# ==================== /start ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    foydalanuvchilar.add(user.id)
    ism = user.first_name or "Mehmon"

    if is_admin(user.id):
        await update.message.reply_text(
            f"👋 Salom, {ism}!\n\n🔑 Admin paneliga xush kelibsiz!\nQuyidagi tugmalardan foydalaning:",
            reply_markup=admin_klaviatura()
        )
    else:
        await update.message.reply_text(
            f"🌿 Salom, {ism}!\n\n🍵 Chayxonaga xush kelibsiz!\nQuyidagi bo'limlardan birini tanlang:",
            reply_markup=asosiy_klaviatura()
        )


# ==================== ADMIN PANELI ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Sizda admin huquqi yo'q!")
        return
    foydalanuvchilar.add(user.id)
    await update.message.reply_text("🔑 Admin paneli\n\nNima qilmoqchisiz?", reply_markup=admin_klaviatura())


# ==================== TAOMLAR KO'RSATISH ====================
async def milliy_taomlar_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foydalanuvchilar.add(update.effective_user.id)
    if not milliy_taomlar:
        await update.message.reply_text("😔 Hozircha milliy taomlar qo'shilmagan.\nTez orada qo'shiladi!", reply_markup=asosiy_klaviatura())
        return

    await update.message.reply_text("🍽 *Milliy taomlar:*", parse_mode="Markdown")
    # Parallel yuborish uchun tasks
    tasks = []
    for i, taom in enumerate(milliy_taomlar, 1):
        text = f"*{i}. {taom['nomi']}*\n💰 Narxi: {taom['narx']} so'm"
        if taom.get("rasm"):
            tasks.append(update.message.reply_photo(photo=taom["rasm"], caption=text, parse_mode="Markdown"))
        else:
            tasks.append(update.message.reply_text(text, parse_mode="Markdown"))
    await asyncio.gather(*tasks)


async def turk_taomlar_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foydalanuvchilar.add(update.effective_user.id)
    if not turk_taomlar:
        await update.message.reply_text("😔 Hozircha turk taomlar qo'shilmagan.\nTez orada qo'shiladi!", reply_markup=asosiy_klaviatura())
        return

    await update.message.reply_text("🥙 *Turk taomlar:*", parse_mode="Markdown")
    tasks = []
    for i, taom in enumerate(turk_taomlar, 1):
        text = f"*{i}. {taom['nomi']}*\n💰 Narxi: {taom['narx']} so'm"
        if taom.get("rasm"):
            tasks.append(update.message.reply_photo(photo=taom["rasm"], caption=text, parse_mode="Markdown"))
        else:
            tasks.append(update.message.reply_text(text, parse_mode="Markdown"))
    await asyncio.gather(*tasks)


async def ichimliklar_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foydalanuvchilar.add(update.effective_user.id)
    if not ichimliklar:
        await update.message.reply_text("😔 Hozircha ichimliklar qo'shilmagan.\nTez orada qo'shiladi!", reply_markup=asosiy_klaviatura())
        return

    await update.message.reply_text("🥤 *Ichimliklar:*", parse_mode="Markdown")
    tasks = []
    for i, ichimlik in enumerate(ichimliklar, 1):
        text = f"*{i}. {ichimlik['nomi']}*\n💰 Narxi: {ichimlik['narx']} so'm"
        if ichimlik.get("rasm"):
            tasks.append(update.message.reply_photo(photo=ichimlik["rasm"], caption=text, parse_mode="Markdown"))
        else:
            tasks.append(update.message.reply_text(text, parse_mode="Markdown"))
    await asyncio.gather(*tasks)


# ==================== TAOM QO'SHISH ====================
async def milliy_taom_qosh_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return ConversationHandler.END
    context.user_data["taom_turi"] = "milliy"
    await update.message.reply_text("🍽 Milliy taom nomini kiriting:")
    return TAOM_NOMI


async def turk_taom_qosh_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return ConversationHandler.END
    context.user_data["taom_turi"] = "turk"
    await update.message.reply_text("🥙 Turk taom nomini kiriting:")
    return TAOM_NOMI


async def taom_nomi_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["yangi_taom_nomi"] = update.message.text
    await update.message.reply_text("💰 Taom narxini kiriting (masalan: 25000):")
    return TAOM_NARX


async def taom_narx_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["yangi_taom_narx"] = update.message.text
    await update.message.reply_text("📸 Taom rasmini yuboring yoki /skip yozing (rasm bo'lmasa):")
    return TAOM_RASM


async def taom_rasm_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rasm = update.message.photo[-1].file_id if update.message.photo else None
    nomi = context.user_data["yangi_taom_nomi"]
    narx = context.user_data["yangi_taom_narx"]
    turi = context.user_data["taom_turi"]
    yangi_taom = {"nomi": nomi, "narx": narx, "rasm": rasm}

    if turi == "milliy":
        milliy_taomlar.append(yangi_taom)
        tur_text = "Milliy taomlar"
    else:
        turk_taomlar.append(yangi_taom)
        tur_text = "Turk taomlar"

    await update.message.reply_text(
        f"✅ *{nomi}* muvaffaqiyatli qo'shildi!\n📂 Bo'lim: {tur_text}\n💰 Narx: {narx} so'm",
        parse_mode="Markdown", reply_markup=admin_klaviatura()
    )
    return ConversationHandler.END


async def taom_skip_rasm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nomi = context.user_data["yangi_taom_nomi"]
    narx = context.user_data["yangi_taom_narx"]
    turi = context.user_data["taom_turi"]
    yangi_taom = {"nomi": nomi, "narx": narx, "rasm": None}

    if turi == "milliy":
        milliy_taomlar.append(yangi_taom)
        tur_text = "Milliy taomlar"
    else:
        turk_taomlar.append(yangi_taom)
        tur_text = "Turk taomlar"

    await update.message.reply_text(
        f"✅ *{nomi}* rasmsiz qo'shildi!\n📂 Bo'lim: {tur_text}\n💰 Narx: {narx} so'm",
        parse_mode="Markdown", reply_markup=admin_klaviatura()
    )
    return ConversationHandler.END


# ==================== ICHIMLIK QO'SHISH ====================
async def ichimlik_qosh_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return ConversationHandler.END
    await update.message.reply_text("🥤 Ichimlik nomini kiriting:")
    return ICHIMLIK_NOMI


async def ichimlik_nomi_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["yangi_ichimlik_nomi"] = update.message.text
    await update.message.reply_text("💰 Ichimlik narxini kiriting (masalan: 8000):")
    return ICHIMLIK_NARX


async def ichimlik_narx_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["yangi_ichimlik_narx"] = update.message.text
    await update.message.reply_text("📸 Ichimlik rasmini yuboring yoki /skip yozing:")
    return ICHIMLIK_RASM


async def ichimlik_rasm_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rasm = update.message.photo[-1].file_id if update.message.photo else None
    nomi = context.user_data["yangi_ichimlik_nomi"]
    narx = context.user_data["yangi_ichimlik_narx"]
    ichimliklar.append({"nomi": nomi, "narx": narx, "rasm": rasm})
    await update.message.reply_text(
        f"✅ *{nomi}* muvaffaqiyatli qo'shildi!\n💰 Narx: {narx} so'm",
        parse_mode="Markdown", reply_markup=admin_klaviatura()
    )
    return ConversationHandler.END


async def ichimlik_skip_rasm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nomi = context.user_data["yangi_ichimlik_nomi"]
    narx = context.user_data["yangi_ichimlik_narx"]
    ichimliklar.append({"nomi": nomi, "narx": narx, "rasm": None})
    await update.message.reply_text(
        f"✅ *{nomi}* rasmsiz qo'shildi!\n💰 Narx: {narx} so'm",
        parse_mode="Markdown", reply_markup=admin_klaviatura()
    )
    return ConversationHandler.END


# ==================== TAOM O'CHIRISH ====================
async def taom_ochir_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return ConversationHandler.END

    if not milliy_taomlar and not turk_taomlar:
        await update.message.reply_text("📭 O'chirish uchun taom yo'q!", reply_markup=admin_klaviatura())
        return ConversationHandler.END

    text = "❌ *Qaysi taomni o'chirmoqchisiz?*\n\n"
    buttons = []

    if milliy_taomlar:
        text += "🍽 *Milliy taomlar:*\n"
        for i, t in enumerate(milliy_taomlar):
            text += f"  M{i+1}. {t['nomi']} - {t['narx']} so'm\n"
            buttons.append([InlineKeyboardButton(f"❌ M{i+1}. {t['nomi']}", callback_data=f"del_milliy_{i}")])

    if turk_taomlar:
        text += "\n🥙 *Turk taomlar:*\n"
        for i, t in enumerate(turk_taomlar):
            text += f"  T{i+1}. {t['nomi']} - {t['narx']} so'm\n"
            buttons.append([InlineKeyboardButton(f"❌ T{i+1}. {t['nomi']}", callback_data=f"del_turk_{i}")])

    buttons.append([InlineKeyboardButton("🚫 Bekor qilish", callback_data="del_cancel")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
    return ConversationHandler.END


async def taom_ochir_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "del_cancel":
        await query.edit_message_text("🚫 Bekor qilindi.")
        return

    if data.startswith("del_milliy_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(milliy_taomlar):
            nomi = milliy_taomlar.pop(idx)["nomi"]
            await query.edit_message_text(f"✅ *{nomi}* o'chirildi!", parse_mode="Markdown")

    elif data.startswith("del_turk_"):
        idx = int(data.split("_")[2])
        if 0 <= idx < len(turk_taomlar):
            nomi = turk_taomlar.pop(idx)["nomi"]
            await query.edit_message_text(f"✅ *{nomi}* o'chirildi!", parse_mode="Markdown")


# ==================== ICHIMLIK O'CHIRISH ====================
async def ichimlik_ochir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return

    if not ichimliklar:
        await update.message.reply_text("📭 O'chirish uchun ichimlik yo'q!", reply_markup=admin_klaviatura())
        return

    text = "❌ *Qaysi ichimlikni o'chirmoqchisiz?*\n\n🥤 *Ichimliklar:*\n"
    buttons = []
    for i, ich in enumerate(ichimliklar):
        text += f"  {i+1}. {ich['nomi']} - {ich['narx']} so'm\n"
        buttons.append([InlineKeyboardButton(f"❌ {i+1}. {ich['nomi']}", callback_data=f"del_ich_{i}")])

    buttons.append([InlineKeyboardButton("🚫 Bekor qilish", callback_data="del_cancel")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


async def ichimlik_ochir_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "del_cancel":
        await query.edit_message_text("🚫 Bekor qilindi.")
        return

    idx = int(query.data.split("_")[2])
    if 0 <= idx < len(ichimliklar):
        nomi = ichimliklar.pop(idx)["nomi"]
        await query.edit_message_text(f"✅ *{nomi}* o'chirildi!", parse_mode="Markdown")


# ==================== REKLAMA ====================
async def reklama_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return ConversationHandler.END

    await update.message.reply_text(
        f"📢 *Reklama yuborish*\n\n👥 Jami foydalanuvchilar: *{len(foydalanuvchilar)}* ta\n\nReklama matnini yozing (yoki /cancel):",
        parse_mode="Markdown"
    )
    return REKLAMA_MATNI


async def reklama_yuborish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matn = update.message.text

    async def send_one(user_id):
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 *Chayxona yangiligi!*\n\n{matn}",
                parse_mode="Markdown"
            )
            return True
        except Exception:
            return False

    # Hammaga parallel yuborish (tez!)
    results = await asyncio.gather(*[send_one(uid) for uid in foydalanuvchilar])
    yuborildi = sum(results)
    xatolik = len(results) - yuborildi

    await update.message.reply_text(
        f"✅ *Reklama yuborildi!*\n\n✔️ Muvaffaqiyatli: {yuborildi} ta\n❌ Xatolik: {xatolik} ta",
        parse_mode="Markdown", reply_markup=admin_klaviatura()
    )
    return ConversationHandler.END


# ==================== STATISTIKA ====================
async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Ruxsat yo'q!")
        return

    await update.message.reply_text(
        f"📊 *Bot statistikasi:*\n\n"
        f"👥 Jami foydalanuvchilar: *{len(foydalanuvchilar)}* ta\n"
        f"🍽 Milliy taomlar: *{len(milliy_taomlar)}* ta\n"
        f"🥙 Turk taomlar: *{len(turk_taomlar)}* ta\n"
        f"🥤 Ichimliklar: *{len(ichimliklar)}* ta",
        parse_mode="Markdown", reply_markup=admin_klaviatura()
    )


# ==================== BEKOR QILISH ====================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🚫 Bekor qilindi.",
        reply_markup=admin_klaviatura() if is_admin(user_id) else asosiy_klaviatura()
    )
    return ConversationHandler.END


async def asosiy_menyu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foydalanuvchilar.add(update.effective_user.id)
    await update.message.reply_text("🏠 Asosiy menyu:", reply_markup=asosiy_klaviatura())


# ==================== MAIN ====================
def main():
    # ✅ concurrent_updates=True - bir vaqtda ko'p foydalanuvchiga javob beradi
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)          # 🚀 Parallel ishlov berish
        .connect_timeout(10)               # ⚡ Ulanish timeout
        .read_timeout(7)                   # ⚡ O'qish timeout
        .write_timeout(5)                  # ⚡ Yozish timeout
        .pool_timeout(3)                   # ⚡ Pool timeout
        .build()
    )

    # Milliy taom qo'shish handler
    milliy_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Milliy taom qo'shish$"), milliy_taom_qosh_start)],
        states={
            TAOM_NOMI: [MessageHandler(filters.TEXT & ~filters.COMMAND, taom_nomi_olish)],
            TAOM_NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, taom_narx_olish)],
            TAOM_RASM: [
                MessageHandler(filters.PHOTO, taom_rasm_olish),
                CommandHandler("skip", taom_skip_rasm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Turk taom qo'shish handler
    turk_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Turk taom qo'shish$"), turk_taom_qosh_start)],
        states={
            TAOM_NOMI: [MessageHandler(filters.TEXT & ~filters.COMMAND, taom_nomi_olish)],
            TAOM_NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, taom_narx_olish)],
            TAOM_RASM: [
                MessageHandler(filters.PHOTO, taom_rasm_olish),
                CommandHandler("skip", taom_skip_rasm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Ichimlik qo'shish handler
    ichimlik_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Ichimlik qo'shish$"), ichimlik_qosh_start)],
        states={
            ICHIMLIK_NOMI: [MessageHandler(filters.TEXT & ~filters.COMMAND, ichimlik_nomi_olish)],
            ICHIMLIK_NARX: [MessageHandler(filters.TEXT & ~filters.COMMAND, ichimlik_narx_olish)],
            ICHIMLIK_RASM: [
                MessageHandler(filters.PHOTO, ichimlik_rasm_olish),
                CommandHandler("skip", ichimlik_skip_rasm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Reklama handler
    reklama_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Reklama yuborish$"), reklama_start)],
        states={
            REKLAMA_MATNI: [MessageHandler(filters.TEXT & ~filters.COMMAND, reklama_yuborish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(milliy_conv)
    app.add_handler(turk_conv)
    app.add_handler(ichimlik_conv)
    app.add_handler(reklama_conv)

    app.add_handler(MessageHandler(filters.Regex("^🍽 Milliy taomlar$"), milliy_taomlar_show))
    app.add_handler(MessageHandler(filters.Regex("^🥙 Turk taomlar$"), turk_taomlar_show))
    app.add_handler(MessageHandler(filters.Regex("^🥤 Ichimliklar$"), ichimliklar_show))
    app.add_handler(MessageHandler(filters.Regex("^❌ Taom o'chirish$"), taom_ochir_start))
    app.add_handler(MessageHandler(filters.Regex("^❌ Ichimlik o'chirish$"), ichimlik_ochir))
    app.add_handler(MessageHandler(filters.Regex("^📊 Statistika$"), statistika))
    app.add_handler(MessageHandler(filters.Regex("^🏠 Asosiy menyu$"), asosiy_menyu))

    # Callback handlerlari
    app.add_handler(CallbackQueryHandler(taom_ochir_callback, pattern="^del_(milliy|turk|cancel)"))
    app.add_handler(CallbackQueryHandler(ichimlik_ochir_callback, pattern="^del_(ich|cancel)"))

    print("🚀 Chayxona bot ishga tushdi (TEZLASHTIRILGAN)...")

    # ✅ TEZLASHTIRILGAN polling sozlamalari
    app.run_polling(
        poll_interval=0,        # ⚡ Kutmasdan darhol yangi so'rov
        timeout=30,             # ⚡ Long polling timeout
        drop_pending_updates=True,  # ⚡ Eski xabarlarni o'tkazib yuborish
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
