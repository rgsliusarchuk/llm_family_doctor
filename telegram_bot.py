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

# Import conversation state management
from src.api.router_assistant import _conversation_states
from src.utils import extract_patient_response

async def handle_edited_diagnosis(update: Update, context: ContextTypes.DEFAULT_TYPE, editing_state: dict, edited_text: str):
    """Handle when a doctor submits an edited diagnosis."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    logger.info(f"Processing edited diagnosis from doctor {user_id}")
    
    try:
        # Get the editing state
        symptoms_hash = editing_state["symptoms_hash"]
        doctor_id = editing_state["doctor_id"]
        
        # Apply output guardrails to the edited diagnosis
        from src.guardrails.llm_guards import guard_output
        guarded_diagnosis = guard_output(edited_text)
        
        # Call the API to save the edited diagnosis
        result = await api_client.edit_diagnosis(symptoms_hash, doctor_id, guarded_diagnosis)
        
        if result:
            # Clear the editing state
            if 'editing_state' in context.user_data:
                del context.user_data['editing_state']
            
            # Send confirmation to the doctor
            await update.message.reply_text(
                "✅ **Діагноз успішно відредаговано та схвалено!**\n\n"
                f"Хеш: `{symptoms_hash}`",
                parse_mode='Markdown'
            )
            
            # Send patient response to the original patient
            if symptoms_hash in patient_diagnosis_map:
                patient_chat_id, patient_user_id = patient_diagnosis_map[symptoms_hash]
                
                # Get the patient response from the edited diagnosis
                patient_response = extract_patient_response(guarded_diagnosis)
                
                # Send the patient response to the original patient
                try:
                    await context.bot.send_message(
                        chat_id=patient_chat_id,
                        text=f"✅ **Ваш діагноз схвалено лікарем:**\n\n{patient_response}",
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent edited patient response to patient {patient_user_id} in chat {patient_chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send edited patient response: {e}")
            else:
                logger.warning(f"Could not find patient info for edited diagnosis hash: {symptoms_hash}")
                
        else:
            await update.message.reply_text("❌ Не вдалося зберегти відредагований діагноз. Спробуйте ще раз.")
            
    except Exception as e:
        logger.error(f"Error handling edited diagnosis: {e}")
        await update.message.reply_text("❌ Помилка обробки відредагованого діагнозу. Спробуйте ще раз.")
        
        # Clear the editing state on error
        if 'editing_state' in context.user_data:
            del context.user_data['editing_state']

# ── Load environment variables ───────────────────────────────────────────────
load_dotenv()

# ── Configuration ───────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
# New → where to push every fresh diagnosis for review
DOCTOR_GROUP_ID = int(os.getenv("DOCTOR_GROUP_ID", "-1"))

# Keep track of which diagnosis-hash we posted in the group
# Maps truncated_hash -> (message_id, full_hash)
diagnosis_message_map: Dict[str, tuple[int, str]] = {}

# Keep track of which patient requested which diagnosis
# Maps symptoms_hash -> (patient_chat_id, patient_user_id)
patient_diagnosis_map: Dict[str, tuple[int, int]] = {}

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
    
    async def approve_diagnosis(self, request_id: str, doctor_id: int) -> Optional[dict]:
        """Approve a diagnosis via the doctor review endpoint."""
        try:
            payload = {
                "doctor_id": doctor_id
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/doctor_review/{request_id}/approve",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error calling approve API: {e}")
            return None
    
    async def edit_diagnosis(self, request_id: str, doctor_id: int, edited_diagnosis: str) -> Optional[dict]:
        """Edit a diagnosis via the doctor review endpoint."""
        try:
            payload = {
                "doctor_id": doctor_id,
                "answer_md": edited_diagnosis
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/doctor_review/{request_id}/edit",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error calling edit API: {e}")
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
/reset - скинути розмову та почати заново

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
   
   💡 **Новий функціонал:** При запиті діагнозу бот може запитати стать та вік для більш точного аналізу.

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

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command to clear conversation state."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Clear conversation state
    key = f"{user_id}:{chat_id}"
    if key in _conversation_states:
        del _conversation_states[key]
    
    await update.message.reply_text("🔄 Розмову скинуто. Можете почати заново!")

async def get_chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chatid command - get current chat ID for debugging."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title or "Private Chat"
    
    message = f"""
📋 **Chat Information:**
• **Chat ID:** `{chat_id}`
• **Chat Type:** {chat_type}
• **Chat Title:** {chat_title}

💡 **To use this as DOCTOR_GROUP_ID:**
Add this to your .env file:
```
DOCTOR_GROUP_ID={chat_id}
```
"""
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages using the assistant façade."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_text = update.message.text
    
    logger.info(f"Received message from user {user_id} in chat {chat_id}: '{message_text}'")
    
    # Check if this is a doctor editing a diagnosis
    if 'editing_state' in context.user_data:
        editing_state = context.user_data['editing_state']
        
        if editing_state.get("action") == "editing_diagnosis":
            # Handle edited diagnosis
            await handle_edited_diagnosis(update, context, editing_state, message_text)
            return
    
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
    
    logger.info(f"API response - Intent: {intent}, Data: {data}")
    logger.info(f"Full API response: {result}")
    
    # Handle different intents
    if intent == "clinic_info":
        # Use the natural language response directly
        await update.message.reply_text(data.get('message', 'Вибачте, сталася помилка.'))
    
    elif intent == "doctor_schedule":
        # Use the natural language response directly
        await update.message.reply_text(data.get('message', 'Вибачте, сталася помилка.'))
    
    elif intent == "diagnose":
        # Check if this is a conversation state message (asking for info) or actual diagnosis
        conversation_state = data.get("conversation_state")
        
        if conversation_state == "collecting_info":
            # This is just asking for patient information, not a diagnosis yet
            message_text = result.get("message", "Не вдалося обробити запит")
            await update.message.reply_text(message_text)
        else:
            # This is an actual diagnosis
            diagnosis = data.get("diagnosis", "Не вдалося згенерувати діагноз")
            symptoms_hash = data.get("symptoms_hash", "")
            
            logger.info(f"Processing diagnosis intent. Symptoms hash: '{symptoms_hash}' (length: {len(symptoms_hash)})")
            logger.info(f"DOCTOR_GROUP_ID: {DOCTOR_GROUP_ID}")
            
            # Validate symptoms_hash for Telegram callback data
            if not symptoms_hash:
                logger.warning(f"Empty symptoms_hash for callback data")
                # Send message to patient that diagnosis is being reviewed
                await update.message.reply_text(
                    "🩺 Ваш запит на діагноз надіслано лікарям для перевірки. "
                    "Ви отримаєте відповідь після схвалення лікарем.",
                    parse_mode='Markdown'
                )
                return
            
            # Truncate symptoms_hash to fit Telegram's 64-byte callback data limit
            # "approve_" = 7 chars, "edit_" = 5 chars, so we can use up to 57 chars for approve
            truncated_hash = symptoms_hash[:50]  # Safe limit for both actions
            
            # Create doctor review buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Схвалити", callback_data=f"approve_{truncated_hash}"),
                    InlineKeyboardButton("✏️ Редагувати", callback_data=f"edit_{truncated_hash}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ① Send message to patient that diagnosis is being reviewed
            await update.message.reply_text(
                "🩺 Ваш запит на діагноз надіслано лікарям для перевірки. "
                "Ви отримаєте відповідь після схвалення лікарем.",
                parse_mode='Markdown'
            )

            # ② Send full diagnosis to doctors' group for review
            if DOCTOR_GROUP_ID != -1:
                logger.info(f"Sending diagnosis to doctors' group {DOCTOR_GROUP_ID}")
                try:
                    group_msg = await context.bot.send_message(
                        chat_id=DOCTOR_GROUP_ID,
                        text=(
                            f"👨‍⚕️ *Нове авто-згенероване заключення* "
                            f"(hash: `{symptoms_hash}`)\n\n{diagnosis}"
                        ),
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    # Remember where the diagnosis lives in the group chat
                    # Use truncated hash for mapping since that's what the callback will use
                    diagnosis_message_map[truncated_hash] = (group_msg.message_id, symptoms_hash)
                    
                    # Store patient information for later use when diagnosis is approved
                    patient_diagnosis_map[symptoms_hash] = (chat_id, user_id)
                    
                    logger.info(f"Successfully sent diagnosis to doctors' group. Message ID: {group_msg.message_id}")
                except Exception as e:
                    logger.error(f"Failed to send diagnosis to doctors' group: {e}")
            else:
                logger.warning("DOCTOR_GROUP_ID is -1, skipping doctors' group message")
    
    else:
        # Fallback for unknown intent
        await update.message.reply_text("❌ Не вдалося розпізнати ваш запит. Спробуйте переформулювати.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks for doctor review."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Received callback data: {data}")
    
    # Validate callback data format
    if not data or '_' not in data:
        logger.error(f"Invalid callback data format: {data}")
        await query.edit_message_text("❌ Помилка обробки кнопки. Спробуйте ще раз.")
        return
    
    try:
        action, request_id = data.split('_', 1)
        
        # Validate action and request_id
        if not action or not request_id:
            logger.error(f"Invalid action or request_id: action='{action}', request_id='{request_id}'")
            await query.edit_message_text("❌ Помилка обробки кнопки. Спробуйте ще раз.")
            return
        
        # For now, we'll use a default doctor ID (in production, get from user context)
        doctor_id = 1  # Default doctor ID
        
        if action == "approve":
            # Get the full hash from our mapping
            full_hash = request_id  # Default to truncated hash
            if request_id in diagnosis_message_map:
                message_id, full_hash = diagnosis_message_map[request_id]
            
            # (a) tell backend with full hash
            result = await api_client.approve_diagnosis(full_hash, doctor_id)
            if result:
                # (b) update group message to show approval
                if DOCTOR_GROUP_ID != -1 and request_id in diagnosis_message_map:
                    try:
                        message_id, _ = diagnosis_message_map[request_id]
                        await context.bot.edit_message_text(
                            chat_id=DOCTOR_GROUP_ID,
                            message_id=message_id,
                            text="✅ *Схвалено лікарем*\n\n" + query.message.text,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Failed to update group message: {e}")
                
                # (c) Send patient response to the original patient
                if full_hash in patient_diagnosis_map:
                    patient_chat_id, patient_user_id = patient_diagnosis_map[full_hash]
                    
                    # Get the patient response directly from cache
                    from src.cache.redis_cache import get_patient_response
                    patient_response = await get_patient_response(full_hash)
                    
                    if patient_response:
                        logger.info(f"Found patient response in cache for hash {full_hash}: {len(patient_response)} chars")
                        
                        # Send the patient response to the original patient
                        try:
                            await context.bot.send_message(
                                chat_id=patient_chat_id,
                                text=f"✅ **Ваш діагноз схвалено лікарем:**\n\n{patient_response}",
                                parse_mode='Markdown'
                            )
                            logger.info(f"Sent patient response to patient {patient_user_id} in chat {patient_chat_id}")
                        except Exception as e:
                            logger.error(f"Failed to send patient response: {e}")
                    else:
                        logger.warning(f"Could not find patient response in cache for hash: {full_hash}")
                        
                        # Try to get the full diagnosis and extract patient response manually
                        from src.cache.redis_cache import get_md
                        from src.utils import extract_patient_response
                        full_diagnosis = await get_md(full_hash)
                        
                        if full_diagnosis:
                            logger.info(f"Found full diagnosis in cache, extracting patient response manually")
                            manual_patient_response = extract_patient_response(full_diagnosis)
                            
                            try:
                                await context.bot.send_message(
                                    chat_id=patient_chat_id,
                                    text=f"✅ **Ваш діагноз схвалено лікарем:**\n\n{manual_patient_response}",
                                    parse_mode='Markdown'
                                )
                                logger.info(f"Sent manually extracted patient response to patient {patient_user_id}")
                            except Exception as e:
                                logger.error(f"Failed to send manually extracted patient response: {e}")
                        else:
                            logger.error(f"Could not find any diagnosis in cache for hash: {full_hash}")
                else:
                    logger.warning(f"Could not find patient info for diagnosis hash: {full_hash}")
                
            else:
                await query.edit_message_text("❌ Не вдалося схвалити діагноз. Спробуйте ще раз.")
        
        elif action == "edit":
            # Get the full hash from our mapping
            full_hash = request_id  # Default to truncated hash
            if request_id in diagnosis_message_map:
                message_id, full_hash = diagnosis_message_map[request_id]
            
            # Get the current diagnosis from cache
            from src.cache.redis_cache import get_md
            current_diagnosis = await get_md(full_hash)
            
            if current_diagnosis:
                # Show the current diagnosis for editing
                edit_message = (
                    f"✏️ **Редагування діагнозу** (hash: `{full_hash}`)\n\n"
                    f"**Поточний діагноз:**\n{current_diagnosis}\n\n"
                    f"📝 Відправте відредагований діагноз у наступному повідомленні.\n"
                    f"💡 Ви можете редагувати як повний діагноз, так і лише секцію 'Коротка відповідь для пацієнта'."
                )
                
                # Store editing state for this doctor
                editing_state = {
                    "action": "editing_diagnosis",
                    "symptoms_hash": full_hash,
                    "original_diagnosis": current_diagnosis,
                    "doctor_id": doctor_id
                }
                
                # Store editing state in context.user_data for this specific user
                context.user_data['editing_state'] = editing_state
                
                await query.edit_message_text(edit_message, parse_mode='Markdown')
            else:
                await query.edit_message_text("❌ Не вдалося знайти діагноз для редагування.")
        
        else:
            logger.warning(f"Unknown action: {action}")
            await query.edit_message_text(
                "❌ Невідома дія."
            )
    
    except Exception as e:
        logger.error(f"Error processing callback data '{data}': {e}")
        await query.edit_message_text("❌ Помилка обробки кнопки. Спробуйте ще раз.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Log more details about the error
    if hasattr(context.error, '__class__'):
        logger.error(f"Error type: {context.error.__class__.__name__}")
    
    # If it's a callback query error, log the callback data
    if update and update.callback_query:
        logger.error(f"Callback query data: {update.callback_query.data}")
        logger.error(f"Callback query from user: {update.callback_query.from_user.id}")
    
    # If it's a message error, log the message text
    if update and update.message:
        logger.error(f"Message text: {update.message.text}")
        logger.error(f"Message from user: {update.message.from_user.id}")

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
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("chatid", get_chat_id_command))
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