import dotenv
import logger as logger

from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
import tg
from telegram.request import HTTPXRequest
from tg import ConversationStates

log = logger.get_logger(__name__)

def main(): 
    api_key = dotenv.get_key(".env", "TELEGRAM_API_KEY")
    if not api_key:
        log.error("TELEGRAM_API_KEY environment variable is not set.")
        return
    
    request = HTTPXRequest(connect_timeout=30, read_timeout=60)
    bot = ApplicationBuilder().token(api_key).request(request).build()

    # conversation handler add manga
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', tg.add)],
        states={
            ConversationStates.CHOOSE_MANGA: [MessageHandler(callback=tg.choose_manga, filters=filters.TEXT)],
            ConversationStates.GET_LAST_CHAPTER: [MessageHandler(callback=tg.get_last_chapter, filters=filters.TEXT)]
        },
        fallbacks=[CommandHandler('cancel', tg.cancel)],
    )
    
    start_handler = CommandHandler('start', tg.help)
    help_handler = CommandHandler('help', tg.help)

    bot.add_handler(start_handler)
    bot.add_handler(help_handler)
    bot.add_handler(conv_handler)

    log.info("Starting the bot...")
    bot.run_polling()

if __name__ == "__main__":
    main()