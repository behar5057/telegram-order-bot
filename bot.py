import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import ReplyKeyboardMarkup

# تحميل المتغيرات
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class OrderBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        if not self.token:
            raise ValueError("لم يتم تعيين BOT_TOKEN في متغيرات البيئة")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر"""
        # الأمر /start
        self.application.add_handler(CommandHandler("start", self.start))
        
        # معالجة الرسائل النصية
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update, context):
        """معالجة أمر /start"""
        user = update.effective_user
        welcome_text = f"""
        👋 أهلاً بك {user.first_name}!
        
        أنا بوت إدارة الطلبات، يمكنني مساعدتك في:
        
        🛍️ **إذا كنت بائعاً:**
        - تسجيل متجر جديد
        - إدارة منتجاتك
        - متابعة طلبات الزبائن
        
        🛒 **إذا كنت زبوناً:**
        - عرض المنتجات
        - تقديم طلبات جديدة
        - متابعة طلبياتك
        
        اختر من القائمة:
        """
        
        keyboard = [
            ['🏪 تسجيل كبائع', '🛒 طلب كزبون'],
            ['📞 المساعدة', 'ℹ️ معلومات عن البوت']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_message(self, update, context):
        """معالجة الرسائل النصية"""
        text = update.message.text
        
        if text == '🏪 تسجيل كبائع':
            await update.message.reply_text("جاري إعداد نظام التسجيل للبائعين...")
            # هنا سأضيف تسجيل البائع
        elif text == '🛒 طلب كزبون':
            await update.message.reply_text("أدخل كود المتجر الذي تريد الطلب منه:")
        else:
            await update.message.reply_text("لم أفهم طلبك، استخدم الأزرار أدناه")

    def run(self):
        """تشغيل البوت"""
        self.application.run_polling(allowed_updates=[])

if __name__ == '__main__':
    bot = OrderBot()
    bot.run()
