import logging
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# BOT TOKEN
TOKEN = "8540310951:AAHVbHdoUPNifw-MU6iyhtECf2Zyf2TlgIc"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"🇮🇳 *नमस्ते {user.first_name}!*\n\n"
        "📱 *Indian Phone Number Info Bot*\n\n"
        "मुझे कोई भी Indian नंबर भेजें:\n"
        "• 9876543210\n"
        "• +919876543210\n"
        "• 919876543210\n\n"
        "मैं यह जानकारी दूंगा:\n"
        "✅ ऑपरेटर का नाम\n"
        "✅ सर्किल/एरिया\n"
        "✅ नंबर वैलिडेशन\n"
        "✅ और भी बहुत कुछ!\n\n"
        "मदद के लिए /help लिखें।",
        parse_mode='Markdown'
    )

# Help command
def help_command(update: Update, context: CallbackContext):
    help_text = """
🆘 *मदद - Indian नंबर बॉट*

*कैसे इस्तेमाल करें:*
1. कोई भी Indian नंबर भेजें
2. सही फॉर्मेट में
3. तुरंत जानकारी पाएं

*स्वीकृत फॉर्मेट:*
✅ 9876543210
✅ +919876543210
✅ 919876543210
✅ 09876543210

*आपको मिलेगा:*
✓ ऑपरेटर (Airtel/Jio/VI/BSNL)
✓ क्षेत्र/सर्किल
✓ वैलिडेशन स्टेटस
✓ टाइमज़ोन
✓ नंबर टाइप

*कमांड्स:*
/start - बॉट शुरू करें
/help - यह मदद देखें

*नोट:* सिर्फ Indian (+91) नंबर सपोर्टेड।
"""
    update.message.reply_text(help_text, parse_mode='Markdown')

# Handle phone numbers
def handle_number(update: Update, context: CallbackContext):
    try:
        text = update.message.text.strip()
        
        # Skip commands
        if text.startswith('/'):
            return
        
        # Clean number
        phone = text.replace(' ', '').replace('-', '')
        
        # Add +91 if needed
        if len(phone) == 10 and phone.isdigit():
            phone = '+91' + phone
        elif phone.startswith('0') and len(phone) == 11:
            phone = '+91' + phone[1:]
        elif phone.startswith('91') and len(phone) == 12:
            phone = '+' + phone
        
        # Check if Indian number
        if not phone.startswith('+91'):
            update.message.reply_text(
                "❌ *सिर्फ Indian नंबर सपोर्टेड!*\n\n"
                "कृपया Indian (+91) नंबर भेजें।\n"
                "उदाहरण: `9876543210`",
                parse_mode='Markdown'
            )
            return
        
        # Parse number
        try:
            parsed = phonenumbers.parse(phone, "IN")
        except:
            update.message.reply_text(
                "❌ *गलत फॉर्मेट!*\n\n"
                "कृपया सही फॉर्मेट use करें:\n"
                "• 9876543210\n"
                "• +919876543210",
                parse_mode='Markdown'
            )
            return
        
        # Check validity
        if not phonenumbers.is_valid_number(parsed):
            update.message.reply_text(
                "❌ *अमान्य नंबर!*\n\n"
                "यह नंबर मौजूद नहीं है या गलत है।",
                parse_mode='Markdown'
            )
            return
        
        # Get information
        operator = carrier.name_for_number(parsed, "en") or "Unknown"
        region = geocoder.description_for_number(parsed, "en") or "India"
        time_zones = timezone.time_zones_for_number(parsed) or ["Asia/Kolkata"]
        
        # Format numbers
        intl_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        natl_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        
        # Prepare response
        response = f"""
📊 *INDIAN नंबर रिपोर्ट*

*मूल जानकारी:*
🔢 नंबर: `{intl_format}`
📞 नेशनल: `{natl_format}`
🏢 ऑपरेटर: {operator}
📍 क्षेत्र: {region}
⏰ टाइमज़ोन: {time_zones[0]}
🇮🇳 देश: India

*वैलिडेशन:*
✅ वैलिड Indian नंबर
✅ +91 कोड सही
✅ सही फॉर्मेट

*नोट:* यह जानकारी सामान्य है।
सटीक लोकेशन ऑपरेटर के पास होती है।
"""
        
        update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text(
            "❌ *त्रुटि हुई!*\n\n"
            "कृपया फिर से कोशिश करें।",
            parse_mode='Markdown'
        )

# Error handler
def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")

# Main function
def main():
    print("=" * 50)
    print("🤖 INDIAN PHONE NUMBER BOT")
    print(f"🔑 Token: {TOKEN[:10]}...")
    print("=" * 50)
    
    try:
        # Create Updater - OLD SYNTAX for version 13.15
        updater = Updater(TOKEN, use_context=True)
        
        # Get dispatcher
        dp = updater.dispatcher
        
        # Add handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_number))
        
        # Add error handler
        dp.add_error_handler(error_handler)
        
        # Start bot
        print("✅ Bot started successfully!")
        print("🔄 Polling for messages...")
        print("🚀 Bot is LIVE! Press Ctrl+C to stop.")
        print("=" * 50)
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your token and internet connection.")

if __name__ == '__main__':
    main()