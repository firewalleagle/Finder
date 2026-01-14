import logging
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# BOT TOKEN - YOUR NEW TOKEN
TOKEN = "8540310951:AAHVbHdoUPNifw-MU6iyhtECf2Zyf2TlgIc"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Indian Operators Database
INDIAN_OPERATORS = {
    'airtel': ['airtel', 'bharti'],
    'jio': ['jio', 'reliance'],
    'vi': ['vi', 'vodafone', 'idea'],
    'bsnl': ['bsnl'],
    'mtnl': ['mtnl'],
    'tata': ['tata', 'docomo'],
}

def detect_operator(phone_number):
    """Detect Indian telecom operator"""
    try:
        # Parse the number
        parsed = phonenumbers.parse(phone_number, "IN")
        operator_name = carrier.name_for_number(parsed, "en")
        
        if operator_name:
            operator_lower = operator_name.lower()
            for op_key, op_names in INDIAN_OPERATORS.items():
                for name in op_names:
                    if name in operator_lower:
                        return op_key.upper()
        
        # If carrier detection fails, try prefix-based detection
        num = phone_number.replace('+91', '').replace('91', '')
        if len(num) >= 4:
            prefix = num[:4]
            
            # Jio prefixes
            if prefix.startswith(('700', '701', '702', '703', '704', '705', '706', '707', '708', '709')):
                return "JIO"
            # Airtel prefixes
            elif prefix.startswith(('980', '981', '982', '983', '984', '985', '986', '987', '988', '989')):
                return "AIRTEL"
            # VI prefixes
            elif prefix.startswith(('990', '991', '992', '993', '994', '995', '996', '997', '998', '999')):
                return "VI"
            # BSNL prefixes
            elif prefix.startswith(('944', '945', '946', '947', '948', '949')):
                return "BSNL"
        
        return operator_name or "Unknown"
    except:
        return "Unknown"

def detect_region(phone_number):
    """Detect region/circle in India"""
    try:
        parsed = phonenumbers.parse(phone_number, "IN")
        region = geocoder.description_for_number(parsed, "en")
        
        if region and 'India' in region:
            return region.replace('India', '').strip() or "India"
        return region or "India"
    except:
        return "India"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 *Welcome {user.first_name}!*\n\n"
        "📱 *Indian Phone Number Info Bot*\n\n"
        "Send me any Indian phone number and I'll provide:\n"
        "• 📞 Operator/Carrier\n"
        "• 📍 Region/Circle\n"
        "• ✅ Validation Status\n"
        "• 🏢 Number Type\n\n"
        "*Examples:*\n"
        "`9876543210`\n"
        "`+919876543210`\n"
        "`919876543210`\n\n"
        "Use /help for more info.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = """
🆘 *HELP - Indian Number Bot*

*How to use:*
1. Send any Indian phone number
2. Use correct format
3. Get instant information

*Accepted Formats:*
✅ 9876543210
✅ +919876543210
✅ 919876543210
✅ 09876543210

*You'll get:*
✓ Operator name (Airtel/Jio/VI/BSNL)
✓ Region/Circle
✓ Number validation
✓ Timezone
✓ Number type

*Commands:*
/start - Start bot
/help - Show this help
/about - About this bot

*Note:* Only Indian (+91) numbers supported.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About this bot"""
    about_text = """
🤖 *About This Bot*

*Version:* 2.0
*Developer:* Custom Bot Solutions
*Purpose:* Indian Phone Number Analysis

*Features:*
• Indian number validation
• Operator detection
• Region identification
• Number type classification

*Technology:*
• Python 3.9+
• python-telegram-bot
• phonenumbers library

*Privacy:*
• No data storage
• Real-time processing
• Privacy compliant

*Contact:* Use /help for support
"""
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number messages"""
    try:
        # Get the message text
        text = update.message.text.strip()
        
        # Skip if it's a command
        if text.startswith('/'):
            return
        
        # Clean the number
        phone = text.replace(' ', '').replace('-', '')
        
        # Add +91 if needed
        if len(phone) == 10 and phone.isdigit():
            phone = '+91' + phone
        elif phone.startswith('0') and len(phone) == 11:
            phone = '+91' + phone[1:]
        elif phone.startswith('91') and len(phone) == 12:
            phone = '+' + phone
        
        # Check if it's an Indian number
        if not phone.startswith('+91'):
            await update.message.reply_text(
                "❌ *Only Indian numbers supported!*\n\n"
                "Please send an Indian (+91) number.\n"
                "Example: `9876543210`",
                parse_mode='Markdown'
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text("🔍 *Analyzing number...*", parse_mode='Markdown')
        
        try:
            # Parse the phone number
            parsed = phonenumbers.parse(phone, "IN")
        except phonenumbers.NumberParseException:
            await processing_msg.edit_text(
                "❌ *Invalid format!*\n\n"
                "Please use correct format:\n"
                "• 9876543210\n"
                "• +919876543210\n"
                "• 919876543210",
                parse_mode='Markdown'
            )
            return
        
        # Check if valid number
        if not phonenumbers.is_valid_number(parsed):
            await processing_msg.edit_text(
                "❌ *Invalid phone number!*\n\n"
                "This number doesn't exist or is incorrect.\n"
                "Please check and try again.",
                parse_mode='Markdown'
            )
            return
        
        # Get all information
        operator = detect_operator(phone)
        region = detect_region(phone)
        
        # Get carrier from library
        carrier_name = carrier.name_for_number(parsed, "en") or "Unknown"
        
        # Get timezone
        time_zones = timezone.time_zones_for_number(parsed) or ["Asia/Kolkata"]
        
        # Get number type
        num_type = phonenumbers.number_type(parsed)
        type_mapping = {
            0: "Fixed Line",
            1: "Mobile",
            2: "Fixed Line or Mobile",
            3: "Toll Free",
            4: "Premium Rate",
            5: "Shared Cost",
            6: "VoIP",
            7: "Personal Number",
            8: "Pager",
            9: "UAN",
            10: "Voice Mail"
        }
        number_type = type_mapping.get(num_type, "Unknown")
        
        # Format numbers
        intl_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        natl_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        
        # Prepare response
        response = f"""
📊 *INDIAN PHONE NUMBER ANALYSIS*

*Basic Information:*
🔢 *Number:* `{intl_format}`
📞 *National:* `{natl_format}`
🏢 *Operator:* {operator}
📍 *Region:* {region}
⏰ *Timezone:* {time_zones[0]}
📱 *Type:* {number_type}

*Validation Results:*
✅ Valid Indian Number
✅ +91 Country Code Verified
✅ Correct Format

*Additional Details:*
• *Carrier Database:* {carrier_name}
• *Possible Circle:* {region.split(',')[0] if ',' in region else region}
• *Number Length:* 10 digits
• *Country:* India 🇮🇳

*Note:* This information is based on public databases.
Personal details require authorized access.
"""
        
        # Add operator-specific info
        if operator == "JIO":
            response += "\n*JIO Info:* 4G/LTE only, VoLTE supported"
        elif operator == "AIRTEL":
            response += "\n*AIRTEL Info:* 2G/3G/4G network, wide coverage"
        elif operator == "VI":
            response += "\n*VI Info:* Vodafone-Idea merged network"
        elif operator == "BSNL":
            response += "\n*BSNL Info:* Government operator, Pan-India coverage"
        
        await processing_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            "❌ *An error occurred!*\n\n"
            "Please try again with a valid Indian number.\n"
            "Example: `9876543210`",
            parse_mode='Markdown'
        )

def main():
    """Start the bot"""
    print("=" * 50)
    print("🤖 INDIAN PHONE NUMBER BOT")
    print("📱 Specialized for Indian (+91) numbers")
    print(f"🔑 Token: {TOKEN[:10]}...")
    print("=" * 50)
    
    try:
        # Create application - FIXED SYNTAX
        application = Application.builder().token(TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        
        # Add message handler for phone numbers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number))
        
        # Start the bot
        print("✅ Bot application created successfully")
        print("🔄 Starting polling...")
        print("🚀 Bot is now running! Press Ctrl+C to stop.")
        print("=" * 50)
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("Please check:")
        print("1. Token is correct")
        print("2. Internet connection")
        print("3. Dependencies installed")

if __name__ == '__main__':
    main()