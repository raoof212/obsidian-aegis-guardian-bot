import os
import logging
import re
from urllib.parse import urlparse

# مكتبة بوت تيليجرام (python-telegram-bot v20+)
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================== إعدادات الأمان ==================
# ⚠️ تحذير أمني: لا تشارك هذا التوكن مع أي شخص.
# إذا تم كشفه سابقاً، اذهب إلى @BotFather فوراً:
# /mybots > @ObsidianAegisBot > API Token > Revoke current token
# ثم استخدم المفتاح الجديد هنا.
import os

# التوكن يُقرأ من متغيرات البيئة، ولا يُكشف في الكود
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("لم يتم العثور على TOKEN في متغيرات البيئة.")

# قائمة سوداء مبدئية بالروابط الخبيثة (سيتم توسيعها لاحقاً)
BLACKLISTED_DOMAINS = [
    "example-scam.com",
    "free-iphone-win.xyz",
    "secure-your-account.info"
]

# ================== إعداد التسجيل (Logging) ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== قلب الذكاء الاصطناعي (محلل التهديدات) ==================
def analyze_threat(text: str) -> tuple[str, str]:
    """
    يحلل النص والروابط ويعيد رسالة منسقة ورمز الأمان.
    يمكن ربطه لاحقاً بـ GPT لتحليل ذكي.
    """
    # استخراج كل الروابط من النص
    urls = re.findall(r'(https?://\S+)', text)
    
    if not urls:
        return "✅ لم أجد أي روابط في رسالتك. إذا كان هناك رابط، أعد إرساله.", "safe"
    
    threats_found = []
    for url in urls:
        domain = urlparse(url).netloc.lower()
        # فحص في القائمة السوداء
        if any(blocked in domain for blocked in BLACKLISTED_DOMAINS):
            threats_found.append(f"🚨 **خطر مؤكد**: {url} (معروف كموقع تصيد)")
        # فحص ذكي بسيط (سيُستبدل بـ GPT لاحقاً)
        elif any(keyword in url.lower() for keyword in ["login", "verify", "account", "password", "free"]):
            threats_found.append(f"⚠️ **حذر شديد**: {url} (يحتوي على كلمات حساسة، قد يكون هجوماً)")
        else:
            threats_found.append(f"ℹ️ **تحليل مبدئي**: {url} (يبدو آمناً، ولكن كن حذراً)")
    
    result = "\n".join(threats_found)
    if "خطر" in result:
        return f"🛡️ **درع إيجيس يحذرك:**\n\n{result}", "danger"
    elif "حذر" in result:
        return f"🛡️ **درع إيجيس ينبهك:**\n\n{result}", "warning"
    else:
        return f"🛡️ **درع إيجيس يطمئنك:**\n\n{result}", "safe"

# ================== أوامر البوت ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب عند /start"""
    welcome_msg = """
🛡️ **أهلاً بك في Obsidian Aegis | Guardian Bot**

أنا درعك البركاني من شركة Obsidian Aegis للأمن السيبراني.

مهمتي بسيطة:
1.  📩 **حوّل لي** أي رسالة مشبوهة أو رابط غريب.
2.  ⚡ **سأحلله** في ثوانٍ باستخدام ذكاء اصطناعي متقدم.
3.  ✅ **سأرد عليك** مباشرة: آمن، احتيال، أو خطر.

🟢 **الباقة المجانية:** تحليل 10 رسائل شهرياً.
🛡️ للترقية لباقة غير محدودة: /upgrade

**حول رسالتك الأولى الآن!**
    """
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رابط الاشتراك بالباقة المدفوعة"""
    msg = "🚀 للترقية إلى الباقة غير المحدودة (1 دولار شهرياً)، تواصل مع @ObsidianAegis_Admin"
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحليل أي رسالة نصية عادية يرسلها المستخدم"""
    user = update.effective_user
    message = update.message.text
    
    # إعلام المستخدم بأن التحليل جارٍ
    await update.message.reply_text("⚡ جاري فحص رسالتك...")
    
    # تحليل التهديد
    analysis, status = analyze_threat(message)
    
    # إضافة تذييل احترافي
    analysis += "\n\n---\n🔒 *فحص بواسطة Obsidian Aegis*"
    
    await update.message.reply_text(analysis, parse_mode='Markdown')

# ================== بدء تشغيل التطبيق ==================
def main():
    """نقطة البداية الرئيسية"""
    # بناء التطبيق وتمرير التوكن
    app = Application.builder().token(TOKEN).build()

    # ربط الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upgrade", upgrade))
    
    # ربط محلل الرسائل (يتعامل مع أي نص ليس أمراً)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # تشغيل البوت في وضع الاستماع المستمر
    print("🛡️ Obsidian Aegis | Guardian Bot نشط وجاهز للعمل.")
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()