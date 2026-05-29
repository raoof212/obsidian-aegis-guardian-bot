import os
import logging
import logging
import re
from urllib.parse import urlparse
from telegram import __version__ as tg_version
print(f"python-telegram-bot version: {tg_version}")
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================== إعدادات الأمان ==================
TOKEN = os.environ.get("TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TOKEN:
    raise ValueError("TOKEN غير موجود في متغيرات البيئة")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY غير موجود في متغيرات البيئة")

# تهيئة مكتبة google-genai الجديدة
from google import genai
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.0-flash"  # النموذج الأحدث (مدفوع الأجر لكن لك 1500 طلب مجاني يومياً)

# قائمة سوداء مبدئية (للاستخدام إذا فشل الذكاء الاصطناعي)
BLACKLISTED_DOMAINS = [
    "example-scam.com",
    "free-iphone-win.xyz",
    "secure-your-account.info"
]

# ================== إعداد التسجيل ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== الذكاء الاصطناعي (Gemini) ==================
async def analyze_with_gemini(text: str) -> str | None:
    prompt = f"""أنت خبير أمن سيبراني متخصص في تحليل الرسائل المشبوهة باللغة العربية.
    حلل الرسالة التالية وحدد:
    - هل هي آمنة أم مشبوهة أم خطيرة؟
    - ما هي علامات الخطر (إن وجدت)؟
    - ما نوع الهجوم المحتمل (تصيد، احتيال، ابتزاز، رابط خبيث...)؟
    - قدم توصية واضحة للمستخدم بالعربية.

    أسلوبك: مختصر، مباشر، ومفهوم للشخص العادي.
    تنسيق الرد: ابدأ مباشرة بالتحليل بدون مقدمات.

    الرسالة:
    {text}
    """

    try:
        logger.info(f"🚀 محاولة استدعاء Gemini بالنموذج: {MODEL_NAME}")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        logger.info(f"✅ استجابة Gemini الخام: {response}")
        result = response.text.strip()
        if not result:
            logger.warning("⚠️ استجابة Gemini فارغة")
            return None
        return f"🧠 **تحليل ذكي:**\n{result}"
    except Exception as e:
        logger.error(f"❌ خطأ في Gemini: {type(e).__name__} - {e}")
        return None

# ================== التحليل التقليدي (احتياطي) ==================
def analyze_traditional(text: str) -> str:
    urls = re.findall(r'(https?://\S+)', text)
    if not urls:
        return "✅ لم أجد أي روابط. الرسالة تبدو عادية، لكن كن حذراً دائماً."

    findings = []
    for url in urls:
        domain = urlparse(url).netloc.lower()
        if any(blocked in domain for blocked in BLACKLISTED_DOMAINS):
            findings.append(f"🚨 رابط خطير (قائمة سوداء): {url}")
        elif any(kw in url.lower() for kw in ["login", "verify", "account", "password", "free"]):
            findings.append(f"⚠️ رابط مشبوه (كلمات حساسة): {url}")
        else:
            findings.append(f"ℹ️ رابط يبدو آمناً: {url}")
    return "\n".join(findings)

# ================== أوامر البوت ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = """
🛡️ **أهلاً بك في Obsidian Aegis | Guardian Bot**
(مُدعّم بالذكاء الاصطناعي)

أنا حارسك الشخصي من شركة Obsidian Aegis.
حوّل لي أي رسالة مشبوهة، وسأحللها فوراً بذكاء خارق.

🟢 الباقة المجانية: تحليل 10 رسائل شهرياً.
🛡️ للترقية: /upgrade

**حول رسالتك الأولى الآن!**
    """
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🚀 للترقية إلى الباقة غير المحدودة (1 دولار شهرياً)، تواصل مع @ObsidianAegis_Admin"
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    await update.message.reply_text("⚡ جاري الفحص بالذكاء الاصطناعي...")

    ai_analysis = await analyze_with_gemini(message_text)

    if ai_analysis:
        final_msg = f"{ai_analysis}\n\n---\n🔒 *فحص بواسطة Obsidian Aegis*"
    else:
        traditional = analyze_traditional(message_text)
        final_msg = f"🛡️ **تحليل تقليدي (احتياطي):**\n{traditional}\n\n---\n🔒 *فحص بواسطة Obsidian Aegis*"

    await update.message.reply_text(final_msg, parse_mode='Markdown')

# ================== بدء التشغيل ==================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upgrade", upgrade))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🛡️ Aegis Guardian (AI-Powered) نشط وجاهز للعمل.")
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()
