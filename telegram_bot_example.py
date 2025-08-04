#!/usr/bin/env python
"""Example Telegram bot for LLM Family Doctor API."""
import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# ── Load environment variables ───────────────────────────────────────────────
load_dotenv()

# ── Configuration ───────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ── Configure logging ───────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── API client ─────────────────────────────────────────────────────────────
class APIClient:
    """Client for the LLM Family Doctor API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
    
    async def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "healthy"
                    return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def generate_diagnosis(
        self, 
        symptoms: str, 
        user_id: str, 
        chat_id: str
    ) -> Optional[dict]:
        """Generate diagnosis using the API."""
        try:
            payload = {
                "symptoms": symptoms,
                "user_id": user_id,
                "chat_id": chat_id,
                "top_k": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/diagnose",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error calling API: {e}")
            return None

# ── Global API client ───────────────────────────────────────────────────────
api_client = APIClient()

# ── Telegram bot handlers ───────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_message = """
🩺 Вітаю! Я LLM-асистент сімейного лікаря.

Я можу допомогти вам з попереднім діагнозом на основі ваших симптомів.

📝 Щоб отримати діагноз, просто опишіть ваші симптоми в повідомленні.

Наприклад:
• "Біль у горлі, температура 38°C, кашель 3 дні"
• "Головний біль, нудота, світлочутливість"
• "Біль у животі, діарея, блювання"

⚠️ Важливо: Це лише попередній діагноз. Завжди консультуйтесь з лікарем для остаточного діагнозу та лікування.
    """
    
    await update.message.reply_text(welcome_message.strip())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_message = """
📋 Доступні команди:

/start - Почати роботу з ботом
/help - Показати цю довідку
/status - Перевірити статус API

💡 Як використовувати:
1. Опишіть ваші симптоми
2. Отримайте попередній діагноз
3. Оцініть діагноз (схвалити/відхилити)

⚠️ Нагадування: Це лише попередній діагноз. Консультуйтесь з лікарем.
    """
    
    await update.message.reply_text(help_message.strip())

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    is_healthy = await api_client.health_check()
    
    if is_healthy:
        status_message = "✅ API сервер працює нормально"
    else:
        status_message = "❌ API сервер недоступний"
    
    await update.message.reply_text(status_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with symptoms."""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    symptoms = update.message.text
    
    # Check if API is healthy
    if not await api_client.health_check():
        await update.message.reply_text(
            "❌ Сервер тимчасово недоступний. Спробуйте пізніше."
        )
        return
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # Generate diagnosis
    result = await api_client.generate_diagnosis(symptoms, user_id, chat_id)
    
    if result:
        diagnosis = result["diagnosis"]
        request_id = result["request_id"]
        
        # Create feedback buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Схвалити", callback_data=f"approve_{request_id}"),
                InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{request_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send diagnosis with feedback buttons
        await update.message.reply_text(
            f"🩺 **Попередній діагноз:**\n\n{diagnosis}\n\n"
            f"⚠️ Це лише попередній діагноз. Консультуйтесь з лікарем.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Не вдалося згенерувати діагноз. Перевірте опис симптомів та спробуйте ще раз."
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks for feedback."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, request_id = data.split('_', 1)
    
    # Send feedback to API
    try:
        payload = {
            "request_id": request_id,
            "status": action
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/feedback",
                json=payload
            ) as response:
                if response.status == 200:
                    if action == "approve":
                        await query.edit_message_text(
                            "✅ Дякуємо за схвалення діагнозу!"
                        )
                    else:
                        await query.edit_message_text(
                            "❌ Дякуємо за відгук. Діагноз відхилено."
                        )
                else:
                    await query.edit_message_text(
                        "❌ Помилка збереження відгуку."
                    )
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        await query.edit_message_text(
            "❌ Помилка збереження відгуку."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")

# ── Main function ───────────────────────────────────────────────────────────
def main():
    """Start the Telegram bot."""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    print("🤖 Starting LLM Family Doctor Telegram Bot...")
    print(f"🌐 API URL: {API_BASE_URL}")
    print("🔧 Press Ctrl+C to stop the bot")
    print("-" * 50)
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n👋 Telegram bot stopped.")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 