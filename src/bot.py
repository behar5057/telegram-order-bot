import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن - سيتم أخذه من Environment Variable
BOT_TOKEN = os.getenv('BOT_TOKEN', '8567098482:AAG2RwierhMVAz4bMHtKiWxBvlAJExOyhN0')

# دوال البوت
async def start(update: Update, context: CallbackContext):
    """معالجة أمر /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"🎉 **مرحباً {user.first_name}!**\n\n"
        "أنا **بوت إدارة الطلبات** 🤖\n\n"
        "✨ **ماذا أقدم:**\n"
        "✅ للبائعين: تسجيل متجر وإدارة طلبات\n"
        "✅ للزبائن: طلب منتجات بسهولة\n\n"
        "📋 **جرب هذه الأوامر:**\n"
        "/register - تسجيل متجر جديد\n"
        "/demo - عرض تجريبي\n"
        "/help - المساعدة\n\n"
        "🚀 **للتجربة السريعة:**\n"
        "اكتب: طلب تجريبي"
    )

async def help_command(update: Update, context: CallbackContext):
    """أمر المساعدة"""
    await update.message.reply_text(
        "📚 **دليل الاستخدام:**\n\n"
        "1. البائع: /register لتسجيل متجر\n"
        "2. يحصل على كود متجر\n"
        "3. الزبون: يدخل الكود ويطلب\n"
        "4. البائع: يتتبع الطلبات\n\n"
        "🔧 **للبدء الآن:**\n"
        "اكتب 'طلب تجريبي' أو /demo"
    )

async def register(update: Update, context: CallbackContext):
    """تسجيل متجر"""
    user_id = update.effective_user.id
    store_code = f"STORE{user_id % 10000:04d}"
    
    await update.message.reply_text(
        f"🏪 **تم إنشاء متجرك!**\n\n"
        f"🔑 **كود المتجر:** `{store_code}`\n"
        f"🔐 **كلمة المرور:** `1234`\n\n"
        f"📤 **أعط هذا الكود للزبائن:**\n"
        f"`{store_code}`\n\n"
        f"💡 **جربه الآن:**\n"
        f"اكتب '{store_code}' في البوت"
    )

async def demo(update: Update, context: CallbackContext):
    """عرض تجريبي"""
    await update.message.reply_text(
        "🛒 **عرض تجريبي:**\n\n"
        "1. **كود المتجر:** STORE1234\n"
        "2. **المنتجات:**\n"
        "   - 📱 هاتف - 500 ريال\n"
        "   - 💻 لابتوب - 2000 ريال\n"
        "   - 🎧 سماعات - 100 ريال\n\n"
        "✍️ **للتجربة:**\n"
        "اكتب 'STORE1234' ثم اختر منتج"
    )

async def handle_message(update: Update, context: CallbackContext):
    """معالجة الرسائل"""
    text = update.message.text
    
    if "طلب تجريبي" in text:
        await update.message.reply_text(
            "🛒 **طلب تجريبي تم استلامه!**\n\n"
            "📦 المنتج: منتج تجريبي\n"
            "💰 السعر: 50 ريال\n"
            "👤 الزبون: مستخدم تجريبي\n"
            "✅ **تم إرسال الطلب للبائع**\n\n"
            "🔙 للعودة: /start"
        )
    
    elif text.startswith("STORE"):
        await update.message.reply_text(
            f"✅ **تم دخول المتجر:** {text}\n\n"
            "📋 **المنتجات:**\n"
            "1. 📱 هاتف - 500 ريال\n"
            "2. 💻 لابتوب - 2000 ريال\n"
            "3. 🎧 سماعات - 100 ريال\n\n"
            "✍️ **للطلب:**\n"
            "اكتب رقم المنتج (1, 2, 3)"
        )
    
    elif text in ["1", "2", "3"]:
        products = {
            "1": "📱 هاتف - 500 ريال",
            "2": "💻 لابتوب - 2000 ريال", 
            "3": "🎧 سماعات - 100 ريال"
        }
        await update.message.reply_text(
            f"✅ **اخترت:** {products[text]}\n\n"
            "📝 **أرسل معلوماتك:**\n"
            "الاسم:\n"
            "الهاتف:\n"
            "العنوان:\n\n"
            "مثال:\n"
            "أحمد محمد\n"
            "0551234567\n"
            "الرياض - حي الملك فهد"
        )
    
    elif "\n" in text and len(text) > 10:
        await update.message.reply_text(
            "🎉 **تم استلام طلبك!**\n\n"
            "📋 **سيتم التواصل معك قريباً**\n\n"
            "✅ **تم إرسال التفاصيل للبائع**\n\n"
            "🔙 /start للعودة"
        )
    
    else:
        await update.message.reply_text(
            "🤔 لم أفهم رسالتك.\n\n"
            "💡 **جرب أحد هذه:**\n"
            "/start - البدء\n"
            "/register - تسجيل متجر\n"
            "/demo - عرض تجريبي\n"
            "/help - المساعدة\n\n"
            "أو اكتب 'طلب تجريبي'"
        )

async def error_handler(update: Update, context: CallbackContext):
    """معالجة الأخطاء"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ حدث خطأ ما.\n"
            "جرب /start لإعادة التشغيل."
        )

def main():
    """الدالة الرئيسية"""
    # إنشاء تطبيق البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("demo", demo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالجة الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info("🚀 بدء تشغيل البوت...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
