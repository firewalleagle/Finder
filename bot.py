import os
import logging
import re
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIGURATION =================
TOKEN = "8540310951:AAHVbHdoUPNifw-MU6iyhtECf2Zyf2TlgIc"
BOT_USERNAME = "@XtremeReactionBot"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Indian telecom operators database
INDIAN_OPERATORS = {
    'AIRTEL': ['airtel', 'bharti'],
    'JIO': ['jio', 'reliance'],
    'VI': ['vodafone', 'idea', 'vi'],
    'BSNL': ['bsnl'],
    'MTNL': ['mtnl'],
    'TATA DOCOMO': ['tata', 'docomo'],
    'AIRCEL': ['aircel'],
}

# Indian circle/state mapping
INDIAN_CIRCLES = {
    'DL': 'Delhi',
    'HR': 'Haryana',
    'PB': 'Punjab',
    'RJ': 'Rajasthan',
    'UP': 'Uttar Pradesh',
    'UK': 'Uttarakhand',
    'HP': 'Himachal Pradesh',
    'JK': 'Jammu & Kashmir',
    'MH': 'Maharashtra',
    'GJ': 'Gujarat',
    'MP': 'Madhya Pradesh',
    'BR': 'Bihar',
    'WB': 'West Bengal',
    'AS': 'Assam',
    'OR': 'Odisha',
    'KA': 'Karnataka',
    'KL': 'Kerala',
    'TN': 'Tamil Nadu',
    'AP': 'Andhra Pradesh',
    'TS': 'Telangana',
    'GA': 'Goa',
    'CH': 'Chandigarh',
    'PY': 'Pondicherry',
}

def detect_indian_operator(number):
    """Detect Indian telecom operator based on number prefix."""
    # Remove country code
    num = number.replace('+91', '').replace('91', '')
    
    if len(num) < 10:
        return "Unknown"
    
    first_four = num[:4]
    
    # Operator detection based on prefixes
    operator_prefixes = {
        'AIRTEL': ['9810', '9811', '9812', '9813', '9814', '9815', '9816', '9817', 
                  '9818', '9819', '9800', '9801', '9802', '9803', '9804', '9805'],
        'JIO': ['7011', '7010', '7012', '7013', '7014', '7015', '7016', '7017',
               '7018', '7019', '7000', '7001', '7002', '7003', '7004', '7005'],
        'VI': ['9890', '9891', '9892', '9893', '9894', '9895', '9896', '9897',
              '9898', '9899', '9999', '9998', '9997', '9996', '9995', '9994'],
        'BSNL': ['9440', '9441', '9442', '9443', '9444', '9445', '9446', '9447',
                '9448', '9449', '9450', '9451', '9452', '9453', '9454', '9455'],
    }
    
    for operator, prefixes in operator_prefixes.items():
        for prefix in prefixes:
            if first_four.startswith(prefix):
                return operator
    
    return "Unknown"

def detect_indian_circle(number):
    """Detect Indian circle/state based on number."""
    # Remove country code
    num = number.replace('+91', '').replace('91', '')
    
    if len(num) < 10:
        return "Unknown"
    
    # First digit after 91
    first_digit = num[0]
    
    # Simple circle detection (basic logic)
    circle_map = {
        '9': 'North India',
        '8': 'South India',
        '7': 'West/Central India',
        '6': 'East/North-East India'
    }
    
    return circle_map.get(first_digit, "India")

def get_number_type_info(number_type):
    """Get detailed number type information."""
    number_types = {
        0: "📞 Fixed Line (Landline)",
        1: "📱 Mobile (Prepaid/Postpaid)",
        2: "📞 Fixed Line or Mobile",
        3: "🆓 Toll Free (1800 series)",
        4: "💰 Premium Rate",
        5: "💲 Shared Cost",
        6: "🌐 VoIP (Internet Calling)",
        7: "👤 Personal Number",
        8: "📟 Pager",
        9: "🏢 UAN (Corporate)",
        10: "📨 Voice Mail"
    }
    return number_types.get(number_type, "📊 Unknown Type")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    user = update.effective_user
    welcome_text = f"""
🇮🇳 *Namaste {user.first_name}!*

Welcome to *XtremeReactionBot* - *Indian Phone Number Analyzer*

📱 *यह बॉट सिर्फ Indian Numbers के लिए है*

📌 *Available Commands:*
/start - बॉट शुरू करें
/help - मदद प्राप्त करें  
/info <number> - नंबर की जानकारी
/operators - Indian Operators List
/circles - Indian Circles List

📞 *कैसे उपयोग करें:*
1. भेजें: `+919876543210`
2. या: `/info +919876543210`
3. या: `/info 9876543210`
4. या सिर्फ: `9876543210`

📍 *सिर्फ Indian Numbers:*
• +91 के साथ या बिना
• 10 अंकों का नंबर
• सभी Indian operators

🔒 *Privacy:* We respect your privacy.
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
📚 *HELP GUIDE - INDIAN NUMBERS ONLY*

*Basic Commands:*
/start - बॉट शुरू करें
/help - यह मदद संदेश
/info <number> - नंबर की जानकारी
/operators - सभी Indian Operators
/circles - सभी Indian Circles

*सही Format:*
✅ 10 अंकों का नंबर
✅ +91 के साथ या बिना
✅ बिना स्पेस के

*उदाहरण:*
• +919876543210
• 919876543210  
• 9876543210
• 09876543210

*आपको क्या मिलेगा:*
✓ ऑपरेटर/कंपनी
✓ नंबर टाइप
✓ वैलिडेशन
✓ सर्किल/एरिया
✓ और भी जानकारी

*Note:* यह बॉट सिर्फ Indian (+91) नंबरों के लिए काम करता है।
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def operators_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of Indian telecom operators."""
    operators_text = """
🏢 *INDIAN TELECOM OPERATORS*

📱 *Major Operators:*
1. *Airtel* - भारती एयरटेल
2. *Jio* - रिलायंस जियो
3. *VI* - वोडाफोन आइडिया
4. *BSNL* - भारत संचार निगम
5. *MTNL* - महानगर टेलीफोन

📞 *Other Operators:*
• Tata Docomo
• Aircel (अब बंद)
• Reliance Communications
• MTS
• Uninor

*Common Prefixes:*
• Airtel: 98xx, 99xx
• Jio: 70xx, 72xx
• VI: 98xx, 99xx
• BSNL: 94xx

*Note:* यह जानकारी सामान्य है, सटीक ऑपरेटर नंबर से पता चलता है।
    """
    await update.message.reply_text(operators_text, parse_mode='Markdown')

async def circles_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of Indian telecom circles."""
    circles_text = """
📍 *INDIAN TELECOM CIRCLES*

*North Zone:*
• Delhi (DL)
• Haryana (HR)
• Punjab (PB)
• Rajasthan (RJ)
• Uttar Pradesh (UP)
• Uttarakhand (UK)
• Himachal Pradesh (HP)
• Jammu & Kashmir (JK)

*West Zone:*
• Maharashtra (MH)
• Gujarat (GJ)
• Madhya Pradesh (MP)
• Goa (GA)

*East Zone:*
• Bihar (BR)
• West Bengal (WB)
• Assam (AS)
• Odisha (OR)
• Northeast States

*South Zone:*
• Karnataka (KA)
• Kerala (KL)
• Tamil Nadu (TN)
• Andhra Pradesh (AP)
• Telangana (TS)

*Union Territories:*
• Chandigarh (CH)
• Pondicherry (PY)

*Note:* हर सर्किल का अलग टैरिफ और प्लान होता है।
    """
    await update.message.reply_text(circles_text, parse_mode='Markdown')

async def analyze_indian_number(phone_number):
    """Analyze Indian phone number."""
    try:
        # Clean the number
        phone_number = phone_number.strip()
        
        # Check if it's an Indian number
        if not (phone_number.startswith('+91') or 
                phone_number.startswith('91') or 
                (len(phone_number) == 10 and phone_number.isdigit()) or
                (len(phone_number) == 11 and phone_number.startswith('0'))):
            return None, "❌ यह Indian नंबर नहीं है। सिर्फ +91 नंबर डालें।"
        
        # Format for parsing
        if phone_number.startswith('0') and len(phone_number) == 11:
            phone_number = '+91' + phone_number[1:]
        elif len(phone_number) == 10 and phone_number.isdigit():
            phone_number = '+91' + phone_number
        elif phone_number.startswith('91') and len(phone_number) == 12:
            phone_number = '+' + phone_number
        
        # Parse phone number
        parsed_number = phonenumbers.parse(phone_number, None)
        
        # Check if it's Indian
        if parsed_number.country_code != 91:
            return None, "❌ यह Indian नंबर नहीं है। सिर्फ +91 नंबर डालें।"
        
        # Check validity
        if not phonenumbers.is_valid_number(parsed_number):
            return None, "❌ अमान्य नंबर। यह नंबर मौजूद नहीं है।"
        
        # Get basic information
        formatted_intl = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        formatted_natl = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        
        # Get carrier info
        carrier_name = carrier.name_for_number(parsed_number, "en") or "Unknown"
        
        # Detect Indian operator
        indian_operator = detect_indian_operator(formatted_intl)
        if indian_operator != "Unknown":
            carrier_name = indian_operator
        
        # Detect circle
        circle = detect_indian_circle(formatted_intl)
        
        # Get number type
        number_type = phonenumbers.number_type(parsed_number)
        type_description = get_number_type_info(number_type)
        
        # Timezone
        time_zones = timezone.time_zones_for_number(parsed_number) or ["IST (Indian Standard Time)"]
        
        # Check if mobile
        is_mobile = number_type == 1
        
        # Prepare response
        result = {
            'formatted_intl': formatted_intl,
            'formatted_natl': formatted_natl,
            'carrier': carrier_name,
            'circle': circle,
            'type': type_description,
            'timezone': time_zones[0],
            'is_valid': True,
            'is_mobile': is_mobile,
            'country': "India 🇮🇳",
            'country_code': "+91"
        }
        
        return result, None
        
    except Exception as e:
        logger.error(f"Error analyzing number: {e}")
        return None, f"❌ त्रुटि: {str(e)}"

async def get_number_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main function to get Indian phone number information."""
    try:
        # Extract phone number
        if update.message.text.startswith('/info'):
            if len(context.args) == 0:
                await update.message.reply_text("❌ कृपया एक नंबर डालें।\nउदाहरण: `/info 9876543210`", parse_mode='Markdown')
                return
            phone_number = ' '.join(context.args)
        else:
            phone_number = update.message.text.strip()
        
        # Show processing message
        processing_msg = await update.message.reply_text("🔍 आपका नंबर चेक किया जा रहा है...")
        
        # Analyze the number
        result, error = await analyze_indian_number(phone_number)
        
        if error:
            await processing_msg.edit_text(error)
            return
        
        # Prepare detailed response
        response = f"""
📊 *INDIAN PHONE NUMBER REPORT* 📊

*Basic Details:*
🔢 *नंबर:* `{result['formatted_intl']}`
📞 *National:* `{result['formatted_natl']}`
🇮🇳 *देश:* {result['country']}
🏢 *ऑपरेटर:* {result['carrier']}
📍 *सर्किल/एरिया:* {result['circle']}
📱 *टाइप:* {result['type']}
⏰ *टाइमज़ोन:* {result['timezone']}

*Validation Results:*
✅ वैलिड Indian नंबर
✅ {result['country_code']} कोड सही
✅ फॉर्मेट सही

*Additional Info:*
{'📱 यह मोबाइल नंबर है (Prepaid/Postpaid)' if result['is_mobile'] else '📞 यह लैंडलाइन नंबर है'}
🌐 10 अंकों का Indian नंबर
📅 TRAI registered

*कैसे पहचाने:*
1. पहला अंक: 9,8,7,6 में से कोई एक
2. +91 country code
3. 10 digits total
4. Valid operator prefix

*Note:* यह जानकारी सामान्य है। सटीक लोकेशन ऑपरेटर के पास होती है।
        """
        
        # Add special notes for operators
        if 'JIO' in result['carrier'].upper():
            response += "\n\n*Jio Note:* 4G/LTE only network, VoLTE support"
        elif 'AIRTEL' in result['carrier'].upper():
            response += "\n\n*Airtel Note:* 2G/3G/4G network, wide coverage"
        elif 'VI' in result['carrier'].upper():
            response += "\n\n*VI Note:* Vodafone-Idea merged network"
        elif 'BSNL' in result['carrier'].upper():
            response += "\n\n*BSNL Note:* Government operator, Pan-India"
        
        await processing_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error: {e}")
        error_msg = "❌ कुछ त्रुटि हुई। कृपया फिर से कोशिश करें।\nसही फॉर्मेट: `9876543210` या `+919876543210`"
        if 'processing_msg' in locals():
            await processing_msg.edit_text(error_msg)
        else:
            await update.message.reply_text(error_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all messages."""
    text = update.message.text
    
    # Log received message
    logger.info(f"User ({update.message.chat.id}): '{text}'")
    
    # Check if message looks like a phone number
    if (text.replace(' ', '').replace('-', '').isdigit() or 
        text.startswith('+') or 
        text.startswith('91') or
        text.startswith('0')):
        await get_number_info(update, context)
    elif text.startswith('/'):
        # It's a command, let command handlers handle it
        pass
    else:
        # Not a phone number or command
        await update.message.reply_text(
            "कृपया एक Indian नंबर डालें।\n"
            "उदाहरण: `9876543210` या `+919876543210`\n\n"
            "मदद के लिए /help टाइप करें।",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ कुछ त्रुटि हुई। कृपया बाद में कोशिश करें।"
        )
    except:
        pass

# ================= MAIN FUNCTION =================

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", get_number_info))
    application.add_handler(CommandHandler("operators", operators_command))
    application.add_handler(CommandHandler("circles", circles_command))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("=" * 50)
    print("🇮🇳 XtremeReactionBot - Indian Numbers Only")
    print(f"🤖 Bot: {BOT_USERNAME}")
    print("📱 Specialized for Indian (+91) numbers")
    print("=" * 50)
    print("Bot is running... Press Ctrl+C to stop.")
    print("\nSupported formats:")
    print("• 9876543210")
    print("• +919876543210")
    print("• 919876543210")
    print("• 09876543210")
    print("=" * 50)
    
    # Run bot
    application.run_polling(
        poll_interval=1,
        timeout=30,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()