import os
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# التوكن ورقم المشرف
BOT_TOKEN = "8567098482:AAFtw5wfoTBEm_6Ld1ePzpfe6GT8GLgde0o"
ADMIN_ID = 6120264201

# قاموس لتخزين البيانات (مؤقت - سنضيف قاعدة بيانات لاحقاً)
stores = {}  # {store_code: store_data}
products = {}  # {store_code: [products]}
orders = {}  # {order_id: order_data}
user_sessions = {}  # {user_id: session_data}

app = Flask(__name__)

# ---------- أوامر البوت ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    
    keyboard = [
        [InlineKeyboardButton("🏪 أنا بائع", callback_data="seller")],
        [InlineKeyboardButton("🛒 أنا زبون", callback_data="buyer")],
        [InlineKeyboardButton("👑 مشرف", callback_data="admin")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"مرحباً {username}! 👋\n"
        "اختر نوع حسابك:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "seller":
        # وضعية البائع
        user_sessions[user_id] = {"mode": "seller", "step": "ask_store_name"}
        await query.edit_message_text("🏪 مرحباً أيها البائع!\nأدخل اسم متجرك:")
    
    elif query.data == "buyer":
        # وضعية الزبون
        user_sessions[user_id] = {"mode": "buyer", "step": "ask_store_code"}
        await query.edit_message_text("🛒 مرحباً أيها الزبون!\nأدخل كود المتجر:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_sessions:
        await update.message.reply_text("❌ لم أتعرف على حالتك. أرسل /start")
        return
    
    session = user_sessions[user_id]
    
    if session["mode"] == "seller" and session["step"] == "ask_store_name":
        # حفظ اسم المتجر
        store_code = f"ST{abs(hash(str(user_id) + text)) % 10000:04d}"
        
        stores[store_code] = {
            "owner_id": user_id,
            "store_name": text,
            "code": store_code,
            "products": []
        }
        
        session["step"] = "done"
        session["store_code"] = store_code
        
        await update.message.reply_text(
            f"✅ تم إنشاء متجرك بنجاح!\n\n"
            f"🏪 اسم المتجر: {text}\n"
            f"🔢 كود المتجر: {store_code}\n\n"
            f"📋 الأوامر المتاحة:\n"
            f"/addproduct - إضافة منتج\n"
            f"/products - عرض منتجاتي\n"
            f"/orders - طلباتي\n"
            f"/code - عرض كود المتجر"
        )
    
    elif session["mode"] == "buyer" and session["step"] == "ask_store_code":
        if text in stores:
            session["step"] = "shopping"
            session["store_code"] = text
            store_name = stores[text]["store_name"]
            
            await update.message.reply_text(
                f"🏪 مرحباً في متجر: {store_name}\n\n"
                f"📋 الأوامر:\n"
                f"/products - عرض المنتجات\n"
                f"/order - تقديم طلب"
            )
        else:
            await update.message.reply_text("❌ كود المتجر غير صحيح. حاول مرة أخرى:")

async def show_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # البحث عن متجر المستخدم
    for code, store in stores.items():
        if store["owner_id"] == user_id:
            await update.message.reply_text(
                f"🔢 كود متجرك: {code}\n\n"
                f"شارك هذا الكود مع زبائنك ليتمكنوا من الطلب من متجرك!"
            )
            return
    
    await update.message.reply_text("❌ ليس لديك متجر مسجل. أرسل /start")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ غير مصرح لك بالدخول")
        return
    
    total_stores = len(stores)
    total_products = sum(len(store["products"]) for store in stores.values())
    
    await update.message.reply_text(
        f"👑 لوحة المشرف\n\n"
        f"📊 الإحصائيات:\n"
        f"• عدد المتاجر: {total_stores}\n"
        f"• عدد المنتجات: {total_products}\n\n"
        f"📋 الأوامر:\n"
        f"/allstores - عرض جميع المتاجر\n"
        f"/allorders - جميع الطلبات"
    )

@app.route('/')
def home():
    return '''
    <html>
        <head><title>Telegram Order Bot</title></head>
        <body>
            <h1>🤖 Telegram Order Bot</h1>
            <p>البوت يعمل بنجاح!</p>
            <p>اذهب إلى Telegram وابحث عن البوت للبدء.</p>
        </body>
    </html>
    '''

def main():
    # إنشاء تطبيق البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("code", show_code))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # تشغيل البوت
    print("🤖 البوت يعمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
