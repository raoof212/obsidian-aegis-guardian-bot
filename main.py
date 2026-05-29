import os
import logging
import re
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================== إعدادات الأمان ==================
TOKEN = os.environ.get("TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TOKEN:
    raise ValueError("TOKEN غير موجود في متغيرات البيئة")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY غير موجود في متغيرات البيئة")

# تهيئة مكتبة google-genai
from google import genai
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.0-flash"

# ================== الثوابت العامة (Pre-compiled) ==================
BLACKLISTED_DOMAINS = [
    "example-scam.com",
    "free-iphone-win.xyz",
    "secure-your-account.info"
]

KEYWORDS_REGEX = re.compile(
    r"\b(?:login|verify|account|password|free|win|gift|confirm|update|"
    r"bank|wallet|urgent|limited|bonus|crypto|bitcoin|otp|paypal|"
    r"security|reset|telegram|whatsapp|prize|reward)\b",
    re.IGNORECASE
)

URGENCY_REGEX = re.compile(
    r"\b(?:urgent|immediately|now|verify now|act now|"
    r"حالاً|فوراً|آخر فرصة|سيتم إغلاق حسابك|تحرك الآن)\b",
    re.IGNORECASE
)

IP_REGEX = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

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
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        result = response.text.strip()
        if not result:
            return None
        return f"🧠 **تحليل ذكي:**\n{result}"
    except Exception as e:
        logger.error(f"خطأ في Gemini: {e}")
        return None

# ================== التحليل التقليدي (احتياطي متقدم) ==================
def analyze_traditional(text: str) -> str:
    urls = re.findall(r'(https?://[^\s]+)', text)
    findings = []
    risk_score = 0

    suspicious_tlds = [
        '.tk', '.ml', '.ga', '.cf',
        '.xyz', '.info', '.top', '.gq'
    ]
    url_shorteners = [
        'bit.ly', 'tinyurl.com',
        't.co', 'goo.gl',
        'ow.ly', 'is.gd',
        'cutt.ly', 'rb.gy'
    ]
    famous_brands = [
        "paypal", "google", "facebook",
        "instagram", "telegram",
        "microsoft", "apple",
        "amazon", "binance"
    ]

    # ================== 1. تحليل النص ==================
    matched_keywords = list(set(KEYWORDS_REGEX.findall(text)))
    if matched_keywords:
        risk_score += len(matched_keywords) * 8
        findings.append(f"⚠️ كلمات تصيد مكتشفة: {', '.join(matched_keywords[:6])}")

    matched_urgency = URGENCY_REGEX.findall(text)
    if matched_urgency:
        risk_score += 20
        findings.append("⚠️ الرسالة تستخدم أسلوب الضغط والاستعجال.")

    # ================== 2. تحليل الروابط ==================
    if not urls:
        if risk_score >= 30:
            findings.append("⚠️ رغم عدم وجود روابط، صياغة الرسالة مشبوهة.")
        else:
            findings.append("✅ لم يتم العثور على روابط داخل الرسالة.")

    for url in urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")

            # القائمة السوداء
            if any(blocked in domain for blocked in BLACKLISTED_DOMAINS):
                findings.append(f"🚨 خطر مؤكد: {domain} موجود بالقائمة السوداء.")
                risk_score += 100
                continue

            # دومين IP
            if IP_REGEX.match(domain):
                findings.append(f"🚨 الرابط يستخدم IP مباشر بدلاً من دومين.")
                risk_score += 45

            # امتدادات خطيرة
            if any(domain.endswith(tld) for tld in suspicious_tlds):
                findings.append(f"⚠️ امتداد نطاق مشبوه: {domain}")
                risk_score += 25

            # روابط مختصرة
            if any(short in domain for short in url_shorteners):
                findings.append(f"⚠️ الرابط مختصر ويخفي الوجهة الحقيقية.")
                risk_score += 20

            # كثرة الشرطات
            if domain.count("-") >= 3:
                findings.append(f"⚠️ الدومين يحتوي شرطات كثيرة (نمط تصيد شائع).")
                risk_score += 15

            # تقليد العلامات التجارية
            for brand in famous_brands:
                if brand in domain and not domain.endswith(f"{brand}.com"):
                    findings.append(f"⚠️ احتمال انتحال علامة تجارية: {domain}")
                    risk_score += 40
                    break

            # روابط طويلة جدًا
            if len(url) > 120:
                findings.append("⚠️ الرابط طويل بشكل غير طبيعي.")
                risk_score += 10

            # وجود @ داخل الرابط
            if "@" in url:
                findings.append("🚨 الرابط يحتوي @ لإخفاء الوجهة الحقيقية.")
                risk_score += 35

            # كلمات حساسة داخل الرابط
            if KEYWORDS_REGEX.findall(url):
                findings.append(f"⚠️ الرابط يحتوي كلمات حساسة.")
                risk_score += 15

        except Exception:
            findings.append(f"⚠️ فشل تحليل الرابط: {url}")
            risk_score += 5

    # ================== 3. التقييم النهائي ==================
    if risk_score >= 120:
        verdict = "🚨 خطر عالي جداً — الرابط أو الرسالة يُحتمل أنها حملة تصيد أو احتيال."
    elif risk_score >= 70:
        verdict = "⚠️ الرسالة مشبوهة بدرجة كبيرة."
    elif risk_score >= 35:
        verdict = "⚠️ توجد مؤشرات مقلقة، تعامل بحذر."
    elif risk_score > 0:
        verdict = "ℹ️ لا توجد مؤشرات خطيرة قوية، لكن الحذر مطلوب."
    else:
        verdict = "✅ لم نكتشف أي مؤشرات خطيرة واضحة."

    findings.append(f"\n{verdict}\n🎯 درجة الخطر: {risk_score}/150")
    return "\n\n".join(findings)

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
        final_msg = f"{ai_analysis}\n\n---\n🔒 فحص بواسطة Obsidian Aegis"
    else:
        traditional = analyze_traditional(message_text)
        final_msg = f"🛡️ تحليل تقليدي (احتياطي):\n{traditional}\n\n---\n🔒 فحص بواسطة Obsidian Aegis"

    try:
        await update.message.reply_text(final_msg, parse_mode='Markdown')
    except Exception:
        await update.message.reply_text(final_msg)

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