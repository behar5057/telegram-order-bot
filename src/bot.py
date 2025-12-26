import logging
import os
import asyncio
import threading
import random
import string
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

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

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

# ========== Telegram Bot Class ==========
class OrderBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ BOT_TOKEN غير موجود في متغيرات البيئة!")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        logging.info("✅ Telegram Bot جاهز للتشغيل")
    
    def generate_store_code(self):
        """توليد كود متجر فريد"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def setup_handlers(self):
        """إعداد جميع معالجات المحادثة"""
        
        # محادثة تسجيل البائع
        seller_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^(🏪 تسجيل كبائع|تسجيل بائع)$'), self.seller_start)],
            states={
                SELLER_REGISTER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.seller_register_name)
                ],
                SELLER_REGISTER_STORE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.seller_register_store)
                ],
                SELLER_REGISTER_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.seller_register_password)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # محادثة تسجيل الدخول للبائع
        seller_login_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^🔐 تسجيل الدخول$'), self.seller_login_start)],
            states={
                SELLER_LOGIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.seller_login_process)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # محادثة إضافة منتج
        add_product_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^➕ إضافة منتج$'), self.add_product_start)],
            states={
                ADD_PRODUCT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_product_name)
                ],
                ADD_PRODUCT_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_product_price)
                ],
                ADD_PRODUCT_DESC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_product_desc)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # محادثة الزبون
        buyer_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^(🛒 طلب كزبون|زبون)$'), self.buyer_start)],
            states={
                BUYER_ENTER_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.buyer_enter_code)
                ],
                BUYER_SELECT_PRODUCT: [
                    CallbackQueryHandler(self.buyer_select_product)
                ],
                BUYER_ENTER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.buyer_enter_name)
                ],
                BUYER_ENTER_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.buyer_enter_phone)
                ],
                BUYER_ENTER_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.buyer_enter_address)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        
        # الأوامر الأساسية
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("dashboard", self.seller_dashboard))
        self.application.add_handler(CommandHandler("orders", self.view_orders))
        
        # إضافة المحادثات
        self.application.add_handler(seller_conv)
        self.application.add_handler(seller_login_conv)
        self.application.add_handler(add_product_conv)
        self.application.add_handler(buyer_conv)
        
        # معالجة الأزرار
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
    
    # ========== الدوال الأساسية ==========
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أمر /start"""
        keyboard = [
            ['🏪 تسجيل كبائع', '🛒 طلب كزبون'],
            ['🔐 تسجيل الدخول', 'ℹ️ المساعدة']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"👋 أهلاً بك {update.effective_user.first_name}!\n\n"
            "أنا بوت إدارة الطلبات، يمكنني مساعدتك في:\n"
            "• تسجيل متجر جديد وإدارة منتجاتك\n"
            "• استقبال طلبات الزبائن وتنظيمها\n"
            "• متابعة جميع طلباتك في مكان واحد\n\n"
            "اختر من القائمة:",
            reply_markup=reply_markup
        )
        return START
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        help_text = """
        📖 **دليل استخدام البوت:**
        
        **للبائعين:**
        1. اختر '🏪 تسجيل كبائع' لتسجيل متجر جديد
        2. بعد التسجيل، ستتلقى كود متجر خاص بك
        3. استخدم '🔐 تسجيل الدخول' للدخول لمتجرك
        4. من لوحة التحكم يمكنك:
           - ➕ إضافة منتجات جديدة
           - 📋 عرض الطلبيات
           - 📊 رؤية إحصائيات متجرك
        
        **للزبائن:**
        1. اختر '🛒 طلب كزبون'
        2. أدخل كود المتجر الذي حصلت عليه من البائع
        3. اختر المنتج المطلوب
        4. املأ معلوماتك
        5. تأكيد الطلب
        
        **الأوامر المتاحة:**
        /start - بدء المحادثة
        /help - عرض هذه المساعدة
        /dashboard - لوحة تحكم البائع
        /orders - عرض الطلبيات
        
        📞 للمساعدة الإضافية، تواصل مع المطور.
        """
        await update.message.reply_text(help_text)
    
    # ========== دوال البائع ==========
    async def seller_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء تسجيل البائع"""
        await update.message.reply_text(
            "🏪 **تسجيل متجر جديد**\n\n"
            "أدخل اسمك الكامل:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SELLER_REGISTER_NAME
    
    async def seller_register_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حفظ اسم البائع"""
        context.user_data['seller_name'] = update.message.text
        await update.message.reply_text("📝 أدخل اسم متجرك:")
        return SELLER_REGISTER_STORE
    
    async def seller_register_store(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حفظ اسم المتجر"""
        context.user_data['store_name'] = update.message.text
        await update.message.reply_text("🔐 اختر كلمة مرور للمتجر:")
        return SELLER_REGISTER_PASSWORD
    
    async def seller_register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إكمال تسجيل البائع"""
        password = update.message.text
        store_code = self.generate_store_code()
        
        # حفظ البائع في قاعدة البيانات
        success = db.add_seller(
            telegram_id=update.effective_user.id,
            store_name=context.user_data['store_name'],
            store_code=store_code,
            password=password
        )
        
        if success:
            keyboard = [['🔐 تسجيل الدخول']]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"🎉 **تم تسجيل متجرك بنجاح!**\n\n"
                f"📋 **معلومات متجرك:**\n"
                f"• اسم المتجر: {context.user_data['store_name']}\n"
                f"• كود المتجر: `{store_code}`\n"
                f"• كلمة المرور: {password}\n\n"
                f"🔑 **احفظ هذه المعلومات!**\n"
                f"📤 **أعط كود المتجر للزبائن:** `{store_code}`\n\n"
                f"الآن يمكنك تسجيل الدخول لإدارة متجرك.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ حدث خطأ في التسجيل. حاول مرة أخرى.")
        
        return ConversationHandler.END
    
    async def seller_login_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء تسجيل الدخول للبائع"""
        await update.message.reply_text(
            "🔐 **تسجيل الدخول للمتجر**\n\n"
            "أدخل كود المتجر الخاص بك:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SELLER_LOGIN
    
    async def seller_login_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تسجيل الدخول"""
        store_code = update.message.text.strip()
        seller = db.get_seller_by_code(store_code)
        
        if seller:
            context.user_data['seller_id'] = seller[0]
            context.user_data['store_name'] = seller[2]
            
            keyboard = [
                ['➕ إضافة منتج', '📋 منتجاتي'],
                ['🛒 الطلبات الجديدة', '📊 الإحصائيات'],
                ['🔙 القائمة الرئيسية']
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"✅ **تم تسجيل الدخول بنجاح!**\n\n"
                f"مرحباً بك في متجر: *{seller[2]}*\n"
                f"اختر من القائمة:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            # حفظ حالة البائع مسجل الدخول
            context.user_data['logged_in'] = True
            return SELLER_DASHBOARD
        else:
            await update.message.reply_text(
                "❌ كود المتجر غير صحيح.\n"
                "تأكد من الكود وأعد المحاولة."
            )
            return ConversationHandler.END
    
    async def seller_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لوحة تحكم البائع"""
        if not context.user_data.get('logged_in'):
            await update.message.reply_text("❌ يجب تسجيل الدخول أولاً.")
            return
        
        seller_id = context.user_data['seller_id']
        store_name = context.user_data['store_name']
        
        # الحصول على الإحصائيات
        products = db.get_products_by_seller(seller_id)
        orders = db.get_orders_for_seller(seller_id)
        
        stats_text = (
            f"📊 **لوحة تحكم {store_name}**\n\n"
            f"• عدد المنتجات: {len(products)}\n"
            f"• عدد الطلبات: {len(orders)}\n"
            f"• الطلبات الجديدة: {len([o for o in orders if o[6] == 'pending'])}\n\n"
            f"اختر من الخيارات:"
        )
        
        keyboard = [
            ['➕ إضافة منتج', '📋 منتجاتي'],
            ['🛒 الطلبات الجديدة', '📊 الإحصائيات'],
            ['📤 تصدير الطلبات', '🔙 القائمة الرئيسية']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # ========== دوال المنتجات ==========
    async def add_product_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء إضافة منتج"""
        if not context.user_data.get('logged_in'):
            await update.message.reply_text("❌ يجب تسجيل الدخول أولاً.")
            return ConversationHandler.END
        
        await update.message.reply_text(
            "🛍️ **إضافة منتج جديد**\n\n"
            "أدخل اسم المنتج:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADD_PRODUCT_NAME
    
    async def add_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حفظ اسم المنتج"""
        context.user_data['product_name'] = update.message.text
        await update.message.reply_text("💰 أدخل سعر المنتج (بالريال):")
        return ADD_PRODUCT_PRICE
    
    async def add_product_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حفظ سعر المنتج"""
        try:
            price = float(update.message.text)
            context.user_data['product_price'] = price
            await update.message.reply_text("📝 أدخل وصف للمنتج (اختياري، أو اكتب 'تخطي'):")
            return ADD_PRODUCT_DESC
        except ValueError:
            await update.message.reply_text("❌ السعر يجب أن يكون رقم. حاول مرة أخرى:")
            return ADD_PRODUCT_PRICE
    
    async def add_product_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إنهاء إضافة المنتج"""
        description = update.message.text if update.message.text != 'تخطي' else ""
        
        product_id = db.add_product(
            seller_id=context.user_data['seller_id'],
            name=context.user_data['product_name'],
            price=context.user_data['product_price'],
            description=description
        )
        
        keyboard = [['➕ إضافة منتج آخر', '🔙 لوحة التحكم']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"✅ **تم إضافة المنتج بنجاح!**\n\n"
            f"🛍️ المنتج: {context.user_data['product_name']}\n"
            f"💰 السعر: {context.user_data['product_price']} ريال\n"
            f"📝 الوصف: {description if description else 'لا يوجد'}\n\n"
            f"يمكنك الآن مشاركة كود متجرك مع الزبائن.",
            reply_markup=reply_markup
        )
        
        # تنظيف البيانات المؤقتة
        context.user_data.pop('product_name', None)
        context.user_data.pop('product_price', None)
        
        return ConversationHandler.END
    
    # ========== دوال الزبون ==========
    async def buyer_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء طلب الزبون"""
        await update.message.reply_text(
            "🛒 **طلب جديد**\n\n"
            "أدخل كود المتجر الذي تريد الشراء منه:",
            reply_markup=ReplyKeyboardRemove()
        )
        return BUYER_ENTER_CODE
    
    async def buyer_enter_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """التحقق من كود المتجر"""
        store_code = update.message.text.strip()
        seller = db.get_seller_by_code(store_code)
        
        if seller:
            context.user_data['seller_id'] = seller[0]
            context.user_data['store_name'] = seller[2]
            
            # الحصول على منتجات المتجر
            products = db.get_products_by_seller(seller[0])
            
            if products:
                keyboard = []
                for product in products:
                    product_id, _, name, price, description, _ = product
                    button_text = f"{name} - {price} ريال"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"product_{product_id}")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"🛍️ **متجر: {seller[2]}**\n\n"
                    f"اختر المنتج الذي تريد طلبه:",
                    reply_markup=reply_markup
                )
                return BUYER_SELECT_PRODUCT
            else:
                await update.message.reply_text("❌ هذا المتجر ليس لديه منتجات بعد.")
                return ConversationHandler.END
        else:
            await update.message.reply_text("❌ كود المتجر غير صحيح. تأكد من الكود وأعد المحاولة.")
            return ConversationHandler.END
    
    async def buyer_select_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار المنتج"""
        query = update.callback_query
        await query.answer()
        
        product_id = int(query.data.split('_')[1])
        context.user_data['product_id'] = product_id
        
        # الحصول على تفاصيل المنتج
        products = db.get_products_by_seller(context.user_data['seller_id'])
        selected_product = None
        for product in products:
            if product[0] == product_id:
                selected_product = product
                break
        
        if selected_product:
            context.user_data['selected_product'] = selected_product
            
            await query.edit_message_text(
                f"🛍️ **اخترت المنتج:**\n\n"
                f"• الاسم: {selected_product[2]}\n"
                f"• السعر: {selected_product[3]} ريال\n"
                f"• الوصف: {selected_product[4] if selected_product[4] else 'لا يوجد'}\n\n"
                f"الآن أدخل اسمك الكامل:"
            )
            return BUYER_ENTER_NAME
    
    async def buyer_enter_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حفظ اسم الزبون"""
        context.user_data['customer_name'] = update.message.text
        await update.message.reply_text("📱 أدخل رقم هاتفك:")
        return BUYER_ENTER_PHONE
    
    async def buyer_enter_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """حفظ رقم هاتف الزبون"""
        context.user_data['customer_phone'] = update.message.text
        await update.message.reply_text("📍 أدخل عنوان التوصيل:")
        return BUYER_ENTER_ADDRESS
    
    async def buyer_enter_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إنهاء الطلب وإرساله"""
        address = update.message.text
        
        # حفظ الطلب في قاعدة البيانات
        order_id = db.add_order(
            product_id=context.user_data['product_id'],
            customer_name=context.user_data['customer_name'],
            customer_phone=context.user_data['customer_phone'],
            customer_address=address
        )
        
        product = context.user_data['selected_product']
        
        # إرسال إشعار للبائع
        seller_id = context.user_data['seller_id']
        seller = db.get_seller_by_code(context.user_data.get('store_code', ''))
        
        keyboard = [['📋 عرض الطلبات']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🎉 **تم استلام طلبك بنجاح!**\n\n"
            f"📋 **تفاصيل طلبك:**\n"
            f"• رقم الطلب: #{order_id}\n"
            f"• المنتج: {product[2]}\n"
            f"• السعر: {product[3]} ريال\n"
            f"• الاسم: {context.user_data['customer_name']}\n"
            f"• الهاتف: {context.user_data['customer_phone']}\n"
            f"• العنوان: {address}\n\n"
            f"✅ سيتم التواصل معك قريباً.\n"
            f"شكراً لثقتك بنا!",
            reply_markup=reply_markup
        )
        
        # تنظيف البيانات المؤقتة
        for key in ['product_id', 'selected_product', 'customer_name', 'customer_phone']:
            context.user_data.pop(key, None)
        
        return ConversationHandler.END
    
    # ========== دوال مساعدة ==========
    async def view_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض الطلبات للبائع"""
        if not context.user_data.get('logged_in'):
            await update.message.reply_text("❌ يجب تسجيل الدخول أولاً.")
            return
        
        seller_id = context.user_data['seller_id']
        orders = db.get_orders_for_seller(seller_id)
        
        if orders:
            orders_text = "📋 **الطلبيات الأخيرة:**\n\n"
            for order in orders[:10]:  # عرض آخر 10 طلبات فقط
                order_id, _, customer_name, customer_phone, customer_address, quantity, status, created_at, product_name, price = order
                orders_text += (
                    f"🆔 #{order_id} - {product_name}\n"
                    f"👤 {customer_name} - 📱 {customer_phone}\n"
                    f"📍 {customer_address}\n"
                    f"💰 {price} ريال - 📅 {created_at[:16]}\n"
                    f"🔸 الحالة: {status}\n"
                    f"{'-'*30}\n"
                )
            
            await update.message.reply_text(orders_text)
        else:
            await update.message.reply_text("📭 لا توجد طلبات حتى الآن.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أزرار Inline"""
        query = update.callback_query
        await query.answer()
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إلغاء المحادثة"""
        await update.message.reply_text(
            "تم الإلغاء.",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
        return ConversationHandler.END
    
    def start(self):
        """بدء تشغيل البوت"""
        import asyncio
        
        async def run():
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # حافظ على التشغيل
            while True:
                await asyncio.sleep(3600)
        
        # تشغيل البوت في خيط منفصل
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run())

# ========== التشغيل الرئيسي ==========
if __name__ == '__main__':
    # إعداد التسجيل
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    try:
        # بدء Flask في خيط منفصل
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("🌐 Flask server started on port 5000")
        
        # بدء Telegram Bot
        bot = OrderBot()
        
        # تشغيل البوت في الخيط الرئيسي
        import asyncio
        asyncio.run(bot.application.run_polling())
        
    except Exception as e:
        logger.error(f"❌ فشل تشغيل البوت: {e}")
