import dotenv
import logger as logger

from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
import tg
from tg import ConversationStates

log = logger.get_logger(__name__)



def main(): 
    
    api_key = dotenv.get_key(".env", "TELEGRAM_API_KEY")
    if not api_key:
        log.error("TELEGRAM_API_KEY environment variable is not set.")
        return
    
    bot = ApplicationBuilder().token(api_key).build()


    # conversation handler add manga
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', tg.add)],
        states={
            ConversationStates.CHOOSE_MANGA: [MessageHandler(callback=tg.choose_manga, filters=filters.TEXT)],
            ConversationStates.GET_LAST_CHAPTER: [MessageHandler(callback=tg.get_last_chapter, filters=filters.TEXT)],
        },
        fallbacks=[CommandHandler('cancel', lambda update, context: update.message.reply_text("Cancelled."))],
    )
    bot.add_handler(conv_handler)
    


    start_handler = CommandHandler('start', tg.help)
    help_handler = CommandHandler('help', tg.help)
    add_helper = CommandHandler('add', tg.add)

    bot.add_handler(start_handler)
    bot.add_handler(help_handler)
    bot.add_handler(add_helper)


    log.info("Starting the bot...")
    bot.run_polling()

if __name__ == "__main__":
    main()