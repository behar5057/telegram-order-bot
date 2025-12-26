import os
import logging
from flask import Flask, render_template_string
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تطبيق Flask
app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Order Bot</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🤖 Telegram Order Bot</h1>
        <p class="status">✅ البوت يعمل بنجاح!</p>
        <p>تم النشر على Render Web Service</p>
        <p>🚀 البوت نشط وجاهز لاستقبال الطلبات</p>
    </body>
    </html>
    ''')

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

@app.route('/ping')
def ping():
    return "pong", 200

# دوال البوت
async def start_command(update: Update, context: CallbackContext):
    """معالجة أمر /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 أهلاً {user.first_name}!\n\n"
        "أنا بوت إدارة الطلبات 🤖\n\n"
        "🎯 **للبائعين:**\n"
        "• سجل متجر جديد\n"
        "• أضف منتجاتك\n"
        "• استلم طلبات الزبائن\n\n"
        "🛒 **للزبائن:**\n"
        "• اختر من المنتجات\n"
        "• قدم طلبك بسهولة\n\n"
        "📋 **الأوامر المتاحة:**\n"
        "/register - تسجيل متجر جديد\n"
        "/login - تسجيل الدخول\n"
        "/add - إضافة منتج\n"
        "/orders - عرض الطلبات\n"
        "/help - المساعدة"
    )

async def help_command(update: Update, context: CallbackContext):
    """أمر المساعدة"""
    await update.message.reply_text(
        "📖 **دليل الاستخدام:**\n\n"
        "1. البائع يسجل بـ /register\n"
        "2. يحصل على كود متجر\n"
        "3. الزبون يدخل الكود ويطلب\n"
        "4. البائع يشرف على الطلبات\n\n"
        "🔧 **للتجربة الآن:**\n"
        "جرب /register لإنشاء متجر تجريبي"
    )

async def register_command(update: Update, context: CallbackContext):
    """تسجيل بائع جديد"""
    await update.message.reply_text(
        "🏪 **تسجيل متجر جديد**\n\n"
        "سيتم إنشاء متجر تجريبي لك:\n"
        "• كود المتجر: TEST123\n"
        "• كلمة المرور: 1234\n\n"
        "📤 أعط هذا الكود للزبائن: TEST123\n\n"
        "🔐 لتسجيل الدخول استخدم: /login"
    )

async def login_command(update: Update, context: CallbackContext):
    """تسجيل دخول البائع"""
    await update.message.reply_text(
        "🔐 **تسجيل الدخول**\n\n"
        "أدخل كود المتجر:\n"
        "(جرب TEST123 للتجربة)"
    )

async def handle_message(update: Update, context: CallbackContext):
    """معالجة الرسائل النصية"""
    text = update.message.text
    
    if text == "TEST123":
        await update.message.reply_text(
            "✅ **تم الدخول لمتجر TEST123**\n\n"
            "📋 **التحكم:**\n"
            "/add - إضافة منتج\n"
            "/orders - عرض الطلبات\n"
            "/products - المنتجات"
        )
    elif "طلب" in text.lower():
        await update.message.reply_text(
            "🛒 **طلب جديد تم استلامه!**\n\n"
            "📦 المنتج: منتج تجريبي\n"
            "💰 السعر: 50 ريال\n"
            "👤 الزبون: مستخدم تجريبي\n"
            "📞 الهاتف: 0555555555\n\n"
            "✅ تم حفظ الطلب بنجاح!"
        )
    else:
        await update.message.reply_text(
            "لم أفهم طلبك. استخدم /start للبدء"
        )

def create_bot():
    """إنشاء وتشغيل البوت"""
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("❌ BOT_TOKEN غير موجود!")
        return None
    
    application = Application.builder().token(token).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("add", register_command))  # مؤقت
    application.add_handler(CommandHandler("orders", register_command))  # مؤقت
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application

def run_bot():
    """تشغيل البوت"""
    logger.info("🚀 بدء تشغيل Telegram Bot...")
    try:
        bot_app = create_bot()
        if bot_app:
            bot_app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"❌ فشل تشغيل البوت: {e}")

# التشغيل الرئيسي
if __name__ == "__main__":
    import threading
    
    # تشغيل البوت في خيط منفصل
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("🤖 Telegram Bot thread started")
    
    # تشغيل Flask
    logger.info("🌐 Starting Flask server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
