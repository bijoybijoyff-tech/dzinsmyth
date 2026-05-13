import os
import logging
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from difflib import get_close_matches

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
EXCEL_FILE = "data.xlsx"
ADMIN_IDS = [int(os.environ.get("ADMIN_ID", "0"))]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_data() -> pd.DataFrame:
    try:
        df = pd.read_excel(EXCEL_FILE, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.fillna("-")
        return df
    except FileNotFoundError:
        logger.error(f"Excel file not found: {EXCEL_FILE}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Excel load error: {e}")
        return pd.DataFrame()


def find_item(df: pd.DataFrame, query: str) -> list[dict]:
    if df.empty:
        return []

    name_col = df.columns[0]
    all_names = df[name_col].tolist()

    exact = df[df[name_col].str.lower() == query.lower()]
    if not exact.empty:
        return exact.to_dict("records")

    close = get_close_matches(query.lower(), [n.lower() for n in all_names], n=5, cutoff=0.4)
    if close:
        mask = df[name_col].str.lower().isin(close)
        return df[mask].to_dict("records")

    mask = df[name_col].str.lower().str.contains(query.lower(), na=False)
    return df[mask].to_dict("records")


def format_item_response(items: list[dict]) -> str:
    if not items:
        return "No item found."

    lines = []
    for item in items:
        cols = list(item.keys())
        lines.append("-" * 28)
        for i, col in enumerate(cols):
            emoji = "📦" if i == 0 else ("💰" if i == 2 else ("🔢" if i == 1 else "📌"))
            lines.append(f"{emoji} *{col}:* {item[col]}")
    lines.append("-" * 28)
    return "\n".join(lines)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()
    cols = ", ".join(df.columns.tolist()) if not df.empty else "File not loaded"
    text = (
        "🤖 *Welcome to Stock Info Bot!*\n\n"
        f"📊 Excel columns: `{cols}`\n\n"
        "🔍 Type any item name to get info.\n\n"
        "📌 *Commands:*\n"
        "/start - Start the bot\n"
        "/list - Show all items\n"
        "/reload - Reload Excel (admin)\n"
        "/upload - Upload new Excel (admin)"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_data()
    if df.empty:
        await update.message.reply_text("No data found.")
        return

    name_col = df.columns[0]
    names = df[name_col].dropna().tolist()

    keyboard = []
    for i in range(0, len(names), 2):
        row = [InlineKeyboardButton(names[i], callback_data=f"item:{names[i]}")]
        if i + 1 < len(names):
            row.append(InlineKeyboardButton(names[i + 1], callback_data=f"item:{names[i+1]}"))
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📋 *Total {len(names)} items found.*\nTap to view details:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def reload_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("This command is for admin only.")
        return
    df = load_data()
    if df.empty:
        await update.message.reply_text("Failed to load Excel.")
    else:
        await update.message.reply_text(
            f"Excel reloaded successfully!\n"
            f"Total {len(df)} rows, {len(df.columns)} columns."
        )


async def upload_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("This command is for admin only.")
        return
    await update.message.reply_text(
        "Please send the new Excel file as attachment.\n"
        "It will be saved automatically as data.xlsx"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    doc = update.message.document
    if not doc.file_name.endswith((".xlsx", ".xls")):
        await update.message.reply_text("Only .xlsx or .xls files are accepted.")
        return

    file = await doc.get_file()
    await file.download_to_drive(EXCEL_FILE)

    df = load_data()
    if df.empty:
        await update.message.reply_text("File saved but failed to load.")
    else:
        await update.message.reply_text(
            f"New Excel uploaded successfully!\n"
            f"Total {len(df)} rows | Columns: {', '.join(df.columns.tolist())}"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    df = load_data()

    if df.empty:
        await update.message.reply_text("Data load failed. Contact admin.")
        return

    items = find_item(df, query)

    if not items:
        name_col = df.columns[0]
        all_names = df[name_col].tolist()
        suggestions = get_close_matches(query.lower(), [n.lower() for n in all_names], n=3, cutoff=0.3)
        if suggestions:
            keyboard = [[InlineKeyboardButton(s.title(), callback_data=f"item:{s}")] for s in suggestions]
            await update.message.reply_text(
                f"*'{query}'* not found. Did you mean:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"*'{query}'* not found.\n"
                "Use /list to see all items.",
                parse_mode="Markdown"
            )
        return

    response = format_item_response(items)
    await update.message.reply_text(response, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("item:"):
        item_name = data[5:]
        df = load_data()
        items = find_item(df, item_name)
        response = format_item_response(items)
        await query.message.reply_text(response, parse_mode="Markdown")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_items))
    app.add_handler(CommandHandler("reload", reload_data))
    app.add_handler(CommandHandler("upload", upload_excel))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
