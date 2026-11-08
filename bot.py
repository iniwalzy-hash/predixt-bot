import os
import io
import logging
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Konfigurasi Logging untuk memantau status bot di Railway Logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Mengambil konfigurasi murni dari Environment Variables Railway
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Validasi keamanan jika variabel belum diset di Railway
if not TELEGRAM_TOKEN:
    raise ValueError("ERROR: TELEGRAM_TOKEN belum diatur di Environment Variables Railway!")
if not GEMINI_API_KEY:
    raise ValueError("ERROR: GEMINI_API_KEY belum diatur di Environment Variables Railway!")

# Inisialisasi Google GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🔥 *Selamat Datang di Predixt Bot!* (@predixtit_bot)\n\n"
        "📸 Kirimkan screenshot jadwal/statistik pertandingan (bisa banyak laga sekaligus),\n"
        "dan sistem akan langsung merilis analisa cepat beserta rekomendasi slip parlay lipatnya!\n\n"
        "✨ _Created by Walzy_"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ *Memindai seluruh pertandingan & menyusun strategi bet...*", parse_mode='Markdown')
    
    try:
        # Unduh foto dari Telegram dan kompres/optimasi ukuran untuk kecepatan proses
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Batasi ukuran maksimum agar proses analisis gambar makin cepat di server
        image.thumbnail((1280, 1280))
        
        # Prompt Analisis Cepat untuk Multi-Match & Pilihan Slip Parlay
        prompt = (
            "Analisis SEMUA pertandingan yang terlihat di dalam screenshot ini dengan cepat dan teliti.\n"
            "Berikan output dalam bahasa Indonesia dengan struktur yang rapi, menarik, dan profesional menggunakan format Markdown.\n\n"
            "Gunakan format struktur berikut:\n\n"
            "⚡ *PREDIXT MULTI-MATCH ANALYSIS* ⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🏟️ *DAFTAR ANALISA PERTANDINGAN:*\n"
            "(Untuk setiap pertandingan yang terdeteksi di gambar, tampilkan dengan format ringkas berikut):\n"
            "• *[Tim A] vs [Tim B]*\n"
            "  - 🎯 *1X2 / Skor:* [Prediksi Hasil & Skor]\n"
            "  - ⚖️ *Handicap (AH):* [Rekomendasi AH]\n"
            "  - ⚽ *Over/Under (OU):* [Rekomendasi O/U]\n"
            "  - 📐 *Corner O/U:* [Rekomendasi Corner]\n"
            "  - 🔥 *Keyakinan:* [Persentase %]\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎟️ *REKOMENDASI SLIP PARLAY (AKUMULASI):*\n"
            "Berdasarkan laga di atas, berikan opsi kombinasi pilihan terbaik:\n"
            "🔸 *Slip 3 Lipat (Treble):* [Sebutkan 3 tim pilihan dengan probabilitas tertinggi]\n"
            "🔸 *Slip 6 Lipat:* [Sebutkan 6 tim pilihan atau kombinasikan opsi aman jika laga < 6]\n"
            "🔸 *Slip 8 Lipat (Max Value):* [Sebutkan kombinasi optimal untuk potensi odds maksimal]\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 *Catatan Analis:* [1 kalimat kesimpulan umum singkat]\n\n"
            "🤖 *Created by Walzy*"
        )
        
        # Kirim ke Gemini API menggunakan model gemini-3.8-flash
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[image, prompt]
        )
        
        # Hapus pesan status loading sementara
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        
        # Kirim hasil analisis ke Telegram
        try:
            await update.message.reply_text(response.text, parse_mode='Markdown')
        except Exception:
            await update.message.reply_text(response.text)
        
    except Exception as e:
        logger.error(f"Gagal memproses gambar di Railway: {str(e)}")
        await update.message.reply_text(f"❌ Gagal memproses gambar. Error: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("🤖 Bot Predixt (@predixtit_bot) sedang berjalan di Railway menggunakan gemini-3.8-flash...")
    app.run_polling()