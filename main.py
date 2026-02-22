import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, Defaults
from datetime import timezone, datetime, timedelta
import io
from collections import defaultdict

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8449962875:AAHTk5I2ykGjbmQsZ5Id2Bh4BeVIQpCDhN0"

API_USER = "1933247091"
API_SECRET = "rR2ErdJQLhY4TqCfGs9UKb6gKrWD6PSN"

SIGHTENGINE_URL = "https://api.sightengine.com/1.0/check.json"

media_timestamps = defaultdict(list)
media_messages = defaultdict(list)
FLOOD_LIMIT = 5
FLOOD_TIME_WINDOW = 60
BAN_DURATION = 30 * 60

flood_warning_sent = defaultdict(bool)

banned_until = defaultdict(lambda: datetime.min)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("➕️ Beni bir Gruba Ekle ➕️", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Merhaba! 👋\n"
        "@GroupSecurityingBot grubunuzu koruyan güçlü bir güvenlik botudur.\n\n"
        "Ne yapar?\n"
        "• Yasaklı (+18, çıplaklık, erotik içerik) medya gönderenleri anında siler ⚠️\n"
        "• Her yasaklı medyada uyarı verir: \"yasaklı medya gönderdi ve bot tarafından silindi\"\n"
        "• 1 dakikada 5+ medya atanları tespit eder ve son 30 dakika boyunca medya gönderemez yapar 🚫 (yalnız 1 kez uyarı verir)\n"
        "• Spam, hızlı medya atanları otomatik temizler\n"
        "• Video ve belgeleri de kontrol eder\n\n"
        "Nasıl kullanılır?\n"
        "1. Beni grubunuza ekleyin\n"
        "2. Yönetici yapın (mesaj silme ve kısıtlama izni verin)\n"
        "3. Güvenli ve temiz bir grup için hazır!\n\n"
        "Sorun yaşarsanız veya istekleriniz varsa yazın! @sovyetci",
        reply_markup=reply_markup
    )

async def check_and_delete_nsfw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or update.effective_chat.type not in ("group", "supergroup"):
        return

    user = update.effective_user
    user_id = user.id
    chat_id = message.chat_id
    now = datetime.utcnow()

    username = user.username if user.username else user.first_name

    if now < banned_until[user_id]:
        try:
            await message.delete()
        except:
            pass
        return

    timestamps = media_timestamps[user_id]
    timestamps = [t for t in timestamps if (now - t).total_seconds() < FLOOD_TIME_WINDOW]
    timestamps.append(now)
    media_timestamps[user_id] = timestamps

    media_messages[user_id].append(message)

    if len(timestamps) > FLOOD_LIMIT:
        if not flood_warning_sent[user_id]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🚫 @{username} birden fazla kez yasaklı medya gönderdi ve 30 dakika boyunca medya gönderemez
