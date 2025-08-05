#!/usr/bin/env python
"""Example Telegram bot for LLM Family Doctor API."""
import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

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

# ── State Machine ───────────────────────────────────────────────────────────
class UserState(str, Enum):
    IDLE = "idle"
    GENDER = "gender"
    AGE = "age"
    DOCTOR = "doctor"
    SYMPTOMS = "symptoms"
    WAITING_DIAGNOSIS = "waiting_diagnosis"

# User session storage (in production, use Redis or DB)
user_sessions: Dict[int, Dict[str, Any]] = {}

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
        gender: str,
        age: int,
        doctor_id: int,
        symptoms: str, 
        user_id: str, 
        chat_id: str
    ) -> Optional[dict]:
        """Generate diagnosis using the API."""
        try:
            payload = {
                "gender": gender,
                "age": age,
                "symptoms": symptoms,
                "top_k": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/diagnoses",
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
    
    async def get_doctors(self) -> Optional[list]:
        """Get list of available doctors."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/doctors") as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Error getting doctors: {e}")
            return None
    
    async def approve_diagnosis(self, request_id: str, doctor_id: int) -> bool:
        """Approve a diagnosis."""
        try:
            payload = {"doctor_id": doctor_id}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/doctor_review/{request_id}/approve",
                    json=payload
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error approving diagnosis: {e}")
            return False
    
    async def edit_diagnosis(self, request_id: str, doctor_id: int, answer_md: str) -> bool:
        """Edit a diagnosis."""
        try:
            payload = {"doctor_id": doctor_id, "answer_md": answer_md}
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/doctor_review/{request_id}/edit",
                    json=payload
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error editing diagnosis: {e}")
            return False

# ── Global API client ───────────────────────────────────────────────────────
api_client = APIClient()

# ── Telegram bot handlers ───────────────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    
    # Initialize user session
    user_sessions[user_id] = {
        "state": UserState.IDLE,
        "gender": None,
        "age": None,
        "doctor_id": None,
        "symptoms": None,
        "session_id": None
    }
    
    welcome_message = """
🩺 Вітаю! Я LLM-асистент сімейного лікаря.

Я допоможу вам з попереднім діагнозом. Спочатку потрібно зібрати необхідну інформацію.

📝 Давайте почнемо! Яка ваша стать?
• чоловік
• жінка  
• інше
    """
    
    # Update user state
    user_sessions[user_id]["state"] = UserState.GENDER
    
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
    """Handle text messages with state machine."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_text = update.message.text
    
    # Get user session
    if user_id not in user_sessions:
        await start_command(update, context)
        return
    
    session = user_sessions[user_id]
    current_state = session["state"]
    
    # Handle different states
    if current_state == UserState.GENDER:
        # Process gender input
        gender_lower = message_text.lower().strip()
        if gender_lower in ["чоловік", "male", "м", "m"]:
            session["gender"] = "male"
            session["state"] = UserState.AGE
            await update.message.reply_text("Дякую! Тепер введіть ваш вік (число від 0 до 120):")
        elif gender_lower in ["жінка", "female", "ж", "f"]:
            session["gender"] = "female"
            session["state"] = UserState.AGE
            await update.message.reply_text("Дякую! Тепер введіть ваш вік (число від 0 до 120):")
        elif gender_lower in ["інше", "other", "о"]:
            session["gender"] = "other"
            session["state"] = UserState.AGE
            await update.message.reply_text("Дякую! Тепер введіть ваш вік (число від 0 до 120):")
        else:
            await update.message.reply_text("Будь ласка, введіть: чоловік, жінка, або інше")
    
    elif current_state == UserState.AGE:
        # Process age input
        try:
            age = int(message_text.strip())
            if age < 0 or age > 120:
                await update.message.reply_text("Вік повинен бути від 0 до 120 років. Спробуйте ще раз:")
            else:
                session["age"] = age
                session["state"] = UserState.DOCTOR
                
                # Get available doctors
                doctors = await api_client.get_doctors()
                if doctors:
                    doctor_list = "\n".join([f"• {doc['id']} - {doc['full_name']} ({doc['position']})" for doc in doctors])
                    await update.message.reply_text(f"Дякую! Ваш вік: {age} років.\n\nВиберіть лікаря:\n{doctor_list}")
                else:
                    await update.message.reply_text("Дякую! Ваш вік: {age} років.\n\nВведіть ID лікаря:")
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть коректний вік (число):")
    
    elif current_state == UserState.DOCTOR:
        # Process doctor selection
        try:
            doctor_id = int(message_text.strip())
            session["doctor_id"] = doctor_id
            session["state"] = UserState.SYMPTOMS
            await update.message.reply_text("Дякую! Тепер опишіть ваші симптоми детально:")
        except ValueError:
            await update.message.reply_text("Будь ласка, введіть коректний ID лікаря (число):")
    
    elif current_state == UserState.SYMPTOMS:
        # Process symptoms and generate diagnosis
        session["symptoms"] = message_text
        session["state"] = UserState.WAITING_DIAGNOSIS
        
        # Check if API is healthy
        if not await api_client.health_check():
            await update.message.reply_text("❌ Сервер тимчасово недоступний. Спробуйте пізніше.")
            session["state"] = UserState.SYMPTOMS
            return
        
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Generate diagnosis
        result = await api_client.generate_diagnosis(
            gender=session["gender"],
            age=session["age"],
            doctor_id=session["doctor_id"],
            symptoms=session["symptoms"],
            user_id=str(user_id),
            chat_id=str(chat_id)
        )
        
        if result:
            diagnosis = result["diagnosis"]
            symptoms_hash = result["symptoms_hash"]
            
            # Store request info for doctor review
            session["request_id"] = symptoms_hash
            
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
            
            # Reset state for next diagnosis
            session["state"] = UserState.IDLE
        else:
            await update.message.reply_text(
                "❌ Не вдалося згенерувати діагноз. Перевірте опис симптомів та спробуйте ще раз."
            )
            session["state"] = UserState.SYMPTOMS
    
    else:
        # Unknown state, restart
        await start_command(update, context)

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
        success = await api_client.approve_diagnosis(request_id, doctor_id)
        if success:
            await query.edit_message_text(
                "✅ Діагноз схвалено лікарем!"
            )
        else:
            await query.edit_message_text(
                "❌ Помилка схвалення діагнозу."
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