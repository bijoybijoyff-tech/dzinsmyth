import os
import logging
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from difflib import get_close_matches

# ===================== কনফিগারেশন =====================
BOT_TOKEN = 8516032711:AAF2M_QHaRUrCjrI8Rbks5kTthdn4M4ERh4       # @BotFather থেকে পান
EXCEL_FILE = "data.xlsx"                 # আপনার এক্সেল ফাইলের নাম
ADMIN_IDS = 6570213822                  # আপনার Telegram User ID (int)
# ======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_data() -> pd.DataFrame:
    """এক্সেল ফাইল লোড করে DataFrame রিটার্ন করে"""
    try:
        df = pd.read_excel(EXCEL_FILE, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.fillna("—")
        return df
    except FileNotFoundError:
        logger.error(f"এক্সেল ফাইল পাওয়া যায়নি: {EXCEL_FILE}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"এক্সেল লোড এরর: {e}")
        return pd.DataFrame()


def find_item(df: pd.DataFrame, query: str) -> list[dict]:
    """
    আইটেম নেইম কলামে query খোঁজে।
    প্রথম কলাম = Item Name হিসেবে ধরা হয়।
    """
    if df.empty:
        return []

    name_col = df.columns[0]
    all_names = df[name_col].tolist()

    # exact match (case-insensitive)
    exact = df[df[name_col].str.lower() == query.lower()]
    if not exact.empty:
        return exact.to_dict("records")

    # partial / close match
    close = get_close_matches(query.lower(), [n.lower() for n in all_names], n=5, cutoff=0.4)
    if close:
        mask = df[name_col].str.lower().isin(close)
        return df[mask].to_dict("records")

    # substring match
    mask = df[name_col].str.lower().str.contains(query.lower(), na=False)
    return df[mask].to_dict("records")


def format_item_response(items: list[dict]) -> str:
    """আইটেম তথ্য সুন্দরভাবে ফরম্যাট করে"""
    if not items:
        return "❌ কোনো আইটেম পাওয়া যায়নি।"

    lines = []
    for item in items:
        cols = list(item.keys())
        lines.append("─" * 28)
        for i, col in enumerate(cols):
            emoji = "📦" if i == 0 else ("💰" if i == 2 else ("🔢" if i == 1 else "📌"))
            lines.append(f"{emoji} *{col}:* {item[col]}")
    lines.append("─" * 28)
    return "\n".join(lines)


# ==================== হ্যান্ডলারস ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()
    cols = ", ".join(df.columns.tolist()) if not df.empty else "ফাইল লোড হয়নি"
    text = (
        "🤖 *স্টক ইনফো বট-এ স্বাগতম!*\n\n"
        f"📊 এক্সেল কলাম: `{cols}`\n\n"
        "🔍 যেকোনো আইটেমের নাম লিখুন, আমি তথ্য দেবো।\n\n"
        "📌 *কমান্ড:*\n"
        "/start — শুরু করুন\n"
        "/list — সব আইটেম দেখুন\n"
        "/reload — এক্সেল রিলোড করুন (admin)\n"
        "/upload — নতুন এক্সেল আপলোড করুন (admin)"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()
    if df.empty:
        await update.message.reply_text("❌ ডেটা পাওয়া যায়নি।")
        return

    name_col = df.columns[0]
    names = df[name_col].dropna().tolist()

    # ইনলাইন বাটন হিসেবে দেখাও
    keyboard = []
    for i in range(0, len(names), 2):
        row = [InlineKeyboardButton(names[i], callback_data=f"item:{names[i]}")]
        if i + 1 < len(names):
            row.append(InlineKeyboardButton(names[i + 1], callback_data=f"item:{names[i+1]}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📋 *মোট {len(names)}টি আইটেম পাওয়া গেছে।*\nযেটি দেখতে চান ট্যাপ করুন:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def reload_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin কমান্ড: এক্সেল রিলোড"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ এই কমান্ড শুধু Admin ব্যবহার করতে পারবেন।")
        return
    df = load_data()
    if df.empty:
        await update.message.reply_text("❌ এক্সেল লোড করতে সমস্যা হয়েছে।")
    else:
        await update.message.reply_text(
            f"✅ এক্সেল সফলভাবে রিলোড হয়েছে!\n"
            f"📊 মোট {len(df)} সারি, {len(df.columns)} কলাম।"
        )


async def upload_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin কমান্ড: নতুন এক্সেল আপলোড করার নির্দেশনা"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ এই কমান্ড শুধু Admin ব্যবহার করতে পারবেন।")
        return
    await update.message.reply_text(
        "📤 নতুন এক্সেল ফাইল এখানে পাঠান (attach করুন)।\n"
        "ফাইলটি স্বয়ংক্রিয়ভাবে `data.xlsx` হিসেবে সেভ হবে।"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin এক্সেল ফাইল পাঠালে সেভ করে"""
    if update.effective_user.id not in ADMIN_IDS:
        return

    doc = update.message.document
    if not doc.file_name.endswith((".xlsx", ".xls")):
        await update.message.reply_text("⚠️ শুধু .xlsx বা .xls ফাইল গ্রহণযোগ্য।")
        return

    file = await doc.get_file()
    await file.download_to_drive(EXCEL_FILE)

    df = load_data()
    if df.empty:
        await update.message.reply_text("❌ ফাইল সেভ হয়েছে কিন্তু লোড করতে সমস্যা।")
    else:
        await update.message.reply_text(
            f"✅ নতুন এক্সেল সফলভাবে আপলোড হয়েছে!\n"
            f"📊 মোট {len(df)} সারি | কলাম: {', '.join(df.columns.tolist())}"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইউজারের টেক্সট মেসেজ হ্যান্ডেল"""
    query = update.message.text.strip()
    df = load_data()

    if df.empty:
        await update.message.reply_text("❌ ডেটা লোড করতে সমস্যা হয়েছে। Admin কে জানান।")
        return

    items = find_item(df, query)

    if not items:
        # কাছাকাছি সাজেশন দেখাও
        name_col = df.columns[0]
        all_names = df[name_col].tolist()
        suggestions = get_close_matches(query.lower(), [n.lower() for n in all_names], n=3, cutoff=0.3)
        if suggestions:
            keyboard = [[InlineKeyboardButton(s.title(), callback_data=f"item:{s}")] for s in suggestions]
            await update.message.reply_text(
                f"🔍 *'{query}'* পাওয়া যায়নি। এগুলো কি খুঁজছেন?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ *'{query}'* নামে কোনো আইটেম পাওয়া যায়নি।\n"
                "/list দিয়ে সব আইটেম দেখুন।",
                parse_mode="Markdown"
            )
        return

    response = format_item_response(items)
    await update.message.reply_text(response, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইনলাইন বাটন ক্লিক হ্যান্ডেল"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("item:"):
        item_name = data[5:]
        df = load_data()
        items = find_item(df, item_name)
        response = format_item_response(items)
        await query.message.reply_text(response, parse_mode="Markdown")


# ===================== মেইন =====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_items))
    app.add_handler(CommandHandler("reload", reload_data))
    app.add_handler(CommandHandler("upload", upload_excel))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("বট চালু হচ্ছে...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
