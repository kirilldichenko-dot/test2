print("РУССКАЯ ВЕРСИЯ БОТА")
"""
Telegram Bot using python-telegram-bot v20+
Requires: TELEGRAM_BOT_TOKEN environment variable
"""

import os
import logging
import random
import string
import ast
import operator
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — Welcome message."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🔐 Генератор пароля", callback_data="menu_password")],
        [InlineKeyboardButton("🎲 Бросить кубик", callback_data="menu_roll")],
        [InlineKeyboardButton("🪙 Подбросить монетку", callback_data="menu_flip")],
        [InlineKeyboardButton("🧮 Калькулятор", callback_data="menu_calc")],
        [InlineKeyboardButton("🕒 Время", callback_data="menu_time")],
        [
            InlineKeyboardButton(
                "🌐 Открыть Web App",
                # TODO: вставьте сюда прод-URL вашего Web App,
                # например: "https://your-project-name.vercel.app"
                web_app=WebAppInfo(url="https://your-project-name.vercel.app"),
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "Я небольшой помощник для повседневных задач.\n"
        "Выбирай действие с помощью кнопок ниже или используй команды через /help 🙂",
        reply_markup=reply_markup,
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses from the main menu."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_password":
        alphabet = string.ascii_letters + string.digits + string.punctuation
        secure_password = "".join(random.SystemRandom().choice(alphabet) for _ in range(12))
        await query.message.reply_text(f"Ваш пароль: {secure_password}")
    elif data == "menu_roll":
        result = random.randint(1, 6)
        await query.message.reply_text(f"🎲 Вы бросили: {result} (1–6)")
    elif data == "menu_flip":
        result = random.choice(["🪙 Орёл!", "🪙 Решка!"])
        await query.message.reply_text(result)
    elif data == "menu_calc":
        await query.message.reply_text(
            "🧮 Чтобы посчитать выражение, отправьте команду в формате:\n"
            "/calc 2 + 2 * 10"
        )
    elif data == "menu_time":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await query.message.reply_text(f"🕒 Время на сервере: {now}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — List all available commands."""
    help_text = (
        "📋 <b>Доступные команды</b>\n\n"
        "/start – краткое приветствие\n"
        "/help  – показать список команд\n\n"
        "🏓 /ping – проверить, что бот на связи\n"
        "🔐 /password – сгенерировать случайный пароль\n"
        "🕒 /time – текущее время на сервере\n"
        "🗣 /echo – повторить ваш текст\n"
        "    Пример: <code>/echo Привет, мир!</code>\n"
        "🎲 /roll – бросить кубик (по умолчанию 1–6)\n"
        "    Пример: <code>/roll 20</code>\n"
        "🪙 /flip – подбросить монетку\n"
        "🧮 /calc – посчитать выражение\n"
        "    Пример: <code>/calc 2 + 2 * 10</code>"
    )
    await update.message.reply_html(help_text)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ping — Connectivity test."""
    await update.message.reply_text("🏓 Понг!")


async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/time — Return the current server time."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"🕒 Время на сервере: {now}")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/echo <text> — Repeat the provided text back to the user."""
    if context.args:
        await update.message.reply_text(" ".join(context.args))
    else:
        await update.message.reply_text("Использование: /echo <ваше сообщение>")


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/password — Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    secure_password = "".join(random.SystemRandom().choice(alphabet) for _ in range(12))
    await update.message.reply_text(f"Ваш пароль: {secure_password}")


async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/roll [N] — Roll a random number from 1 to N (default 6)."""
    try:
        n = int(context.args[0]) if context.args else 6
        if n < 2:
            await update.message.reply_text("⚠️ Число должно быть не меньше 2.")
            return
        result = random.randint(1, n)
        await update.message.reply_text(f"🎲 Вы бросили: {result} (1–{n})")
    except (ValueError, IndexError):
        await update.message.reply_text("Использование: /roll <число>  например, /roll 20")


async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/flip — Flip a coin."""
    result = random.choice(["🪙 Орёл!", "🪙 Решка!"])
    await update.message.reply_text(result)


# Safe math operators for /calc
_CALC_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    """Recursively evaluate a safe math AST node."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _CALC_OPERATORS:
        return _CALC_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _CALC_OPERATORS:
        return _CALC_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/calc <expr> — Evaluate a math expression safely."""
    if not context.args:
        await update.message.reply_text("Использование: /calc <выражение>  например, /calc 2 + 2 * 10")
        return
    expr = " ".join(context.args)
    try:
        tree = ast.parse(expr, mode="eval")
        result = _safe_eval(tree)
        # Format: hide .0 for whole numbers
        formatted = int(result) if isinstance(result, float) and result.is_integer() else round(result, 10)
        await update.message.reply_text(f"🧮 {expr} = {formatted}")
    except ZeroDivisionError:
        await update.message.reply_text("⚠️ Деление на ноль.")
    except Exception:
        await update.message.reply_text("⚠️ Некорректное выражение. Поддерживаются только простые арифметические операции.")


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any plain-text message that is not a command."""
    await update.message.reply_text(
        "Я пока не понимаю обычные сообщения. Попробуйте команду /help, чтобы увидеть список команд."
    )


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and optionally notify the user."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    # Notify the user only when an Update object is available
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз позже."
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is not set.\n"
            "Export it before running the bot:\n"
            "  export TELEGRAM_BOT_TOKEN='8027767093:AAH0kx1uqZIrrDcJ6GKI3KTUfR-NrnmPntA'"
        )

    # Build the Application (handles networking, updates, and lifecycle)
    app = Application.builder().token(token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("password", password))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("flip", flip))
    app.add_handler(CommandHandler("calc", calc))

    # Callback query handler for inline keyboard menu
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))

    # Catch-all handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    # Register the error handler
    app.add_error_handler(error_handler)

    logger.info("Bot is running. Press Ctrl+C to stop.")
    # Start polling Telegram's servers for updates
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
