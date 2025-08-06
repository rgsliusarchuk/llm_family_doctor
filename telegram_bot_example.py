#!/usr/bin/env python
"""Example Telegram bot for LLM Family Doctor API using the new assistant façade endpoint."""
import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

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
    """Client for the LLM Family Doctor API using the assistant façade."""
    
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
    
    async def send_message(
        self, 
        text: str,
        user_id: str,
        chat_id: str
    ) -> Optional[dict]:
        """Send message to assistant façade endpoint."""
        try:
            payload = {
                "text": text,
                "user_id": user_id,
                "chat_id": chat_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/assistant/message",
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

# Global API client
api_client = APIClient()

# ── Bot handlers ───────────────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_message = """
🤖 **Ласкаво просимо до LLM Family Doctor!**

Я - ваш віртуальний помічник, який може:

🏥 **Інформація про клініку** - адреса, години роботи, послуги
👨‍⚕️ **Розклад лікарів** - доступність та графік роботи
🩺 **Попередній діагноз** - аналіз симптомів на основі медичних протоколів

Просто напишіть ваше повідомлення, і я допоможу вам!

**Приклади:**
• "Де знаходиться ваша клініка?"
• "Коли працює доктор Іванов?"
• "У мене головний біль і температура"
• "Моя дитина кашляє"

/help - довідка
/status - статус сервісу
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_message = """
📋 **Довідка по командам:**

/start - почати роботу
/help - ця довідка
/status - перевірити статус сервісу

**Як користуватися:**

1. **Інформація про клініку:**
   - "Де знаходиться клініка?"
   - "Які години роботи?"
   - "Які послуги надаєте?"

2. **Розклад лікарів:**
   - "Коли працює доктор Петренко?"
   - "Розклад доктора Іванова"
   - "Доступність лікаря 123"

3. **Попередній діагноз:**
   - "У мене головний біль"
   - "Дитина має температуру"
   - "Відчуваю біль у животі"

⚠️ **Важливо:** Попередній діагноз не замінює консультацію з лікарем!
"""
    
    await update.message.reply_text(
        help_message,
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    if await api_client.health_check():
        status_message = "✅ API сервер працює нормально"
    else:
        status_message = "❌ API сервер недоступний"
    
    await update.message.reply_text(status_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages using the assistant façade."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_text = update.message.text
    
    # Check if API is healthy
    if not await api_client.health_check():
        await update.message.reply_text("❌ Сервер тимчасово недоступний. Спробуйте пізніше.")
        return
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    # Send message to assistant façade
    result = await api_client.send_message(
        text=message_text,
        user_id=str(user_id),
        chat_id=str(chat_id)
    )
    
    if not result:
        await update.message.reply_text("❌ Не вдалося обробити ваше повідомлення. Спробуйте ще раз.")
        return
    
    intent = result.get("intent")
    data = result.get("data", {})
    
    # Handle different intents
    if intent == "clinic_info":
        # Format clinic information
        clinic_info = f"""
🏥 **Інформація про клініку:**

📍 **Адреса:** {data.get('address', 'Не вказано')}
🕒 **Години роботи:** {data.get('opening_hours', 'Не вказано')}
📋 **Послуги:** {data.get('services', 'Не вказано')}
"""
        if data.get('phone'):
            clinic_info += f"📞 **Телефон:** {data['phone']}\n"
        
        await update.message.reply_text(clinic_info, parse_mode='Markdown')
    
    elif intent == "doctor_schedule":
        # Format doctor schedule
        doctor_info = f"""
👨‍⚕️ **Інформація про лікаря:**

👤 **ПІБ:** {data.get('full_name', 'Не вказано')}
🏥 **Посада:** {data.get('position', 'Не вказано')}
📅 **Розклад:** {data.get('schedule', 'Не вказано')}
"""
        await update.message.reply_text(doctor_info, parse_mode='Markdown')
    
    elif intent == "diagnose":
        # Handle diagnosis with approval buttons
        diagnosis = data.get("diagnosis", "Не вдалося згенерувати діагноз")
        symptoms_hash = data.get("symptoms_hash", "")
        
        # Create doctor review buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Схвалити", callback_data=f"approve_{symptoms_hash}"),
                InlineKeyboardButton("✏️ Редагувати", callback_data=f"edit_{symptoms_hash}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send diagnosis with doctor review buttons
        await update.message.reply_text(
            f"🩺 **Попередній діагноз:**\n\n{diagnosis}\n\n"
            f"⚠️ Це лише попередній діагноз. Консультуйтесь з лікарем.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    else:
        # Fallback for unknown intent
        await update.message.reply_text("❌ Не вдалося розпізнати ваш запит. Спробуйте переформулювати.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks for doctor review."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, request_id = data.split('_', 1)
    
    # For now, we'll use a default doctor ID (in production, get from user context)
    doctor_id = 1  # Default doctor ID
    
    if action == "approve":
        # Approve the diagnosis
        # Note: This would need to be implemented in the assistant router
        await query.edit_message_text(
            "✅ Діагноз схвалено лікарем!"
        )
    
    elif action == "edit":
        # For editing, we'll need to implement a more complex flow
        # For now, just acknowledge the edit request
        await query.edit_message_text(
            "✏️ Функція редагування буде доступна в наступній версії."
        )
    
    else:
        await query.edit_message_text(
            "❌ Невідома дія."
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
    
    print("🤖 Starting LLM Family Doctor Telegram Bot (Assistant Façade)...")
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