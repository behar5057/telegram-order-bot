import logging
import os
import asyncio
from telegram.ext import Application, CommandHandler
import threading
from flask import Flask, render_template_string

# ========== جزء Flask للويب (مطلوب لـ Web Service) ==========
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
        <p>البوت جاهز لاستقبال الطلبات على Telegram</p>
    </body>
    </html>
    ''')

@app.route('/health')
def health():
    return {"status": "healthy", "service": "telegram-bot"}, 200

def run_flask():
    """تشغيل Flask في خيط منفصل"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# ========== جزء Telegram Bot ==========
class OrderBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        if not self.token:
            raise ValueError("BOT_TOKEN غير موجود!")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        logging.info("✅ Telegram Bot جاهز للتشغيل")
    
    def setup_handlers(self):
        async def start(update, context):
            await update.message.reply_text("🚀 البوت يعمل على Render Web Service!")
        
        self.application.add_handler(CommandHandler("start", start))
    
    async def run_bot(self):
        """تشغيل البوت"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # حافظ على تشغيل البوت
        while True:
            await asyncio.sleep(3600)
    
    def start(self):
        """بدء البوت في خيط منفصل"""
        import asyncio
        asyncio.run(self.run_bot())

# ========== التشغيل الرئيسي ==========
if __name__ == '__main__':
    # إعداد التسجيل
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # بدء Flask في خيط منفصل
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("🌐 Flask server started on port 5000")
    
    # بدء Telegram Bot
    try:
        bot = OrderBot()
        bot.start()
    except Exception as e:
        logging.error(f"❌ فشل تشغيل البوت: {e}")
