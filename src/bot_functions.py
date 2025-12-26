import logging
import random
import string
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ConversationHandler, ContextTypes
)

from database import db

logger = logging.getLogger(__name__)

# ========== دوال مساعدة ==========
def generate_store_code():
    """توليد كود متجر فريد"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ========== دوال البوت ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    📞 للمساحة الإضافية، تواصل مع المطور.
    """
    await update.message.reply_text(help_text)

async def seller_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء تسجيل البائع"""
    await update.message.reply_text(
        "🏪 **تسجيل متجر جديد**\n\n"
        "أدخل اسمك الكامل:",
        reply_markup=ReplyKeyboardRemove()
    )
    return 1  # SELLER_REGISTER_NAME

async def seller_register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ اسم البائع"""
    context.user_data['seller_name'] = update.message.text
    await update.message.reply_text("📝 أدخل اسم متجرك:")
    return 2  # SELLER_REGISTER_STORE

async def seller_register_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ اسم المتجر"""
    context.user_data['store_name'] = update.message.text
    await update.message.reply_text("🔐 اختر كلمة مرور للمتجر:")
    return 3  # SELLER_REGISTER_PASSWORD

async def seller_register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إكمال تسجيل البائع"""
    password = update.message.text
    store_code = generate_store_code()
    
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

async def seller_login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء تسجيل الدخول للبائع"""
    await update.message.reply_text(
        "🔐 **تسجيل الدخول للمتجر**\n\n"
        "أدخل كود المتجر الخاص بك:",
        reply_markup=ReplyKeyboardRemove()
    )
    return 4  # SELLER_LOGIN

async def seller_login_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        context.user_data['logged_in'] = True
        return 5  # SELLER_DASHBOARD
    else:
        await update.message.reply_text(
            "❌ كود المتجر غير صحيح.\n"
            "تأكد من الكود وأعد المحاولة."
        )
        return ConversationHandler.END

async def seller_dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /dashboard"""
    if not context.user_data.get('logged_in'):
        await update.message.reply_text("❌ يجب تسجيل الدخول أولاً. استخدم '🔐 تسجيل الدخول'")
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
        f"استخدم الأزرار للتحكم."
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إضافة منتج"""
    if not context.user_data.get('logged_in'):
        await update.message.reply_text("❌ يجب تسجيل الدخول أولاً.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🛍️ **إضافة منتج جديد**\n\n"
        "أدخل اسم المنتج:",
        reply_markup=ReplyKeyboardRemove()
    )
    return 6  # ADD_PRODUCT_NAME

async def add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ اسم المنتج"""
    context.user_data['product_name'] = update.message.text
    await update.message.reply_text("💰 أدخل سعر المنتج (بالريال):")
    return 7  # ADD_PRODUCT_PRICE

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ سعر المنتج"""
    try:
        price = float(update.message.text)
        context.user_data['product_price'] = price
        await update.message.reply_text("📝 أدخل وصف للمنتج (اختياري، أو اكتب 'تخطي'):")
        return 8  # ADD_PRODUCT_DESC
    except ValueError:
        await update.message.reply_text("❌ السعر يجب أن يكون رقم. حاول مرة أخرى:")
        return 7

async def add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def buyer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء طلب الزبون"""
    await update.message.reply_text(
        "🛒 **طلب جديد**\n\n"
        "أدخل كود المتجر الذي تريد الشراء منه:",
        reply_markup=ReplyKeyboardRemove()
    )
    return 9  # BUYER_ENTER_CODE

async def buyer_enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            return 10  # BUYER_SELECT_PRODUCT
        else:
            await update.message.reply_text("❌ هذا المتجر ليس لديه منتجات بعد.")
            return ConversationHandler.END
    else:
        await update.message.reply_text("❌ كود المتجر غير صحيح. تأكد من الكود وأعد المحاولة.")
        return ConversationHandler.END

async def buyer_select_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        return 11  # BUYER_ENTER_NAME

async def buyer_enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ اسم الزبون"""
    context.user_data['customer_name'] = update.message.text
    await update.message.reply_text("📱 أدخل رقم هاتفك:")
    return 12  # BUYER_ENTER_PHONE

async def buyer_enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ رقم هاتف الزبون"""
    context.user_data['customer_phone'] = update.message.text
    await update.message.reply_text("📍 أدخل عنوان التوصيل:")
    return 13  # BUYER_ENTER_ADDRESS

async def buyer_enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    # تنظيف البيانات المؤقتة
    for key in ['product_id', 'selected_product', 'customer_name', 'customer_phone']:
        context.user_data.pop(key, None)
    
    keyboard = [['🏠 القائمة الرئيسية']]
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
    
    return ConversationHandler.END

async def view_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /orders"""
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

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار Inline"""
    query = update.callback_query
    await query.answer()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المحادثة"""
    await update.message.reply_text(
        "تم الإلغاء.",
        reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
    )
    return ConversationHandler.END

# ========== إعداد المعالجات ==========
def setup_bot_handlers(application):
    """إعداد جميع معالجات البوت"""
    
    # محادثة تسجيل البائع
    seller_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(🏪 تسجيل كبائع)$'), seller_start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_register_name)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_register_store)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_register_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # محادثة تسجيل الدخول للبائع
    seller_login_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^🔐 تسجيل الدخول$'), seller_login_start)],
        states={
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, seller_login_process)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # محادثة إضافة منتج
    add_product_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ إضافة منتج$'), add_product_start)],
        states={
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_name)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_price)],
            8: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_product_desc)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # محادثة الزبون
    buyer_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(🛒 طلب كزبون)$'), buyer_start)],
        states={
            9: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_enter_code)],
            10: [CallbackQueryHandler(buyer_select_product_callback)],
            11: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_enter_name)],
            12: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_enter_phone)],
            13: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_enter_address)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # الأوامر الأساسية
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dashboard", seller_dashboard_command))
    application.add_handler(CommandHandler("orders", view_orders_command))
    
    # إضافة المحادثات
    application.add_handler(seller_conv)
    application.add_handler(seller_login_conv)
    application.add_handler(add_product_conv)
    application.add_handler(buyer_conv)
    
    # معالجة الأزرار
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # معالجة الرسائل النصية العامة
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text == '🏠 القائمة الرئيسية':
            await start_command(update, context)
        elif text == '🔙 القائمة الرئيسية':
            await start_command(update, context)
        elif text == '🔙 لوحة التحكم':
            if context.user_data.get('logged_in'):
                await seller_dashboard_command(update, context)
            else:
                await update.message.reply_text("❌ يجب تسجيل الدخول أولاً.")
        elif text == '📋 منتجاتي':
            if context.user_data.get('logged_in'):
                seller_id = context.user_data['seller_id']
                products = db.get_products_by_seller(seller_id)
                if products:
                    products_text = "📦 **منتجات متجرك:**\n\n"
                    for product in products:
                        _, _, name, price, description, _ = product
                        products_text += f"🛍️ {name}\n💰 {price} ريال\n📝 {description if description else 'لا يوجد وصف'}\n{'─'*30}\n"
                    await update.message.reply_text(products_text)
                else:
                    await update.message.reply_text("📦 لا توجد منتجات في متجرك بعد.")
            else:
                await update.message.reply_text("❌ يجب تسجيل الدخول أولاً.")
        elif text == '🛒 الطلبات الجديدة':
            await view_orders_command(update, context)
        elif text == '📊 الإحصائيات':
            if context.user_data.get('logged_in'):
                await seller_dashboard_command(update, context)
            else:
                await update.message.reply_text("❌ يجب تسجيل الدخول أولاً.")
        else:
            await update.message.reply_text("استخدم الأزرار أو الأوامر المتاحة.")
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ تم إعداد معالجات البوت بنجاح")
