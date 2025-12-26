import logging
import os
import threading
from datetime import datetime
from flask import Flask, render_template_string
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ConversationHandler, ContextTypes
)

from database import db

# ========== Flask Web Server ==========
app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Order Bot</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { color: #28a745; font-weight: bold; font-size: 24px; margin: 20px 0; }
            .info { color: #666; margin: 10px 0; }
            .stats { display: flex; justify-content: space-around; margin: 30px 0; }
            .stat-box { background: #f8f9fa; padding: 15px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 متجر الطلبات على Telegram</h1>
            <div class="status">✅ البوت يعمل بنجاح!</div>
            <p class="info">تم النشر على Render Web Service</p>
            <p class="info">البوت جاهز لاستقبال الطلبات</p>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>🛍️ النظام يشمل:</h3>
                    <p>• تسجيل البائعين</p>
                    <p>• إدارة المنتجات</p>
                    <p>• استقبال الطلبات</p>
                    <p>• تنظيم الطلبيات</p>
                </div>
            </div>
            
            <p>🚀 ابدأ بإرسال /start في البوت</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/health')
def health():
    return {"status": "healthy", "service": "telegram-order-bot", "timestamp": datetime.now().isoformat()}, 200

@app.route('/ping')
def ping():
    return "pong", 200

# ========== Telegram Bot States ==========
(
    START,
    SELLER_REGISTER_NAME,
    SELLER_REGISTER_STORE,
    SELLER_REGISTER_PASSWORD,
    SELLER_LOGIN,
    SELLER_DASHBOARD,
    ADD_PRODUCT_NAME,
    ADD_PRODUCT_PRICE,
    ADD_PRODUCT_DESC,
    BUYER_ENTER_CODE,
    BUYER_SELECT_PRODUCT,
    BUYER_ENTER_NAME,
    BUYER_ENTER_PHONE,
    BUYER_ENTER_ADDRESS,
) = range(14)

# ========== Telegram Bot Functions ==========
# (هذه دوال البوت، سيتم استيرادها من ملف منفصل)

def create_bot():
    """إنشاء وتشغيل البوت"""
    token = os.getenv('BOT_TOKEN')
    if not token:
        raise ValueError("❌ BOT_TOKEN غير موجود في متغيرات البيئة!")
    
    application = Application.builder().token(token).build()
    
    # استيراد دوال البوت من ملف منفصل لتجنب المشاكل
    from bot_functions import setup_bot_handlers
    setup_bot_handlers(application)
    
    return application

def run_bot():
    """تشغيل البوت في خيط منفصل"""
    logging.info("🤖 بدء تشغيل Telegram Bot...")
    try:
        bot_app = create_bot()
        bot_app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logging.error(f"❌ فشل تشغيل البوت: {e}")

# ========== التشغيل الرئيسي ==========
if __name__ == '__main__':
    # إعداد التسجيل
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    try:
        # بدء Telegram Bot في خيط منفصل
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("🤖 Telegram Bot thread started")
        
        # بدء Flask في الخيط الرئيسي
        logger.info("🌐 Starting Flask server on port 5000")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
    except Exception as e:
        logger.error(f"❌ فشل تشغيل التطبيق: {e}")
