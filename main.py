import dotenv
import logger as logger

from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
import tg
from telegram.request import HTTPXRequest
from tg import AddMangaConversationStates, ManageMangaConversationStates

log = logger.get_logger(__name__)

def main(): 
    api_key = dotenv.get_key(".env", "TELEGRAM_API_KEY")
    if not api_key:
        log.error("TELEGRAM_API_KEY environment variable is not set.")
        return
    
    request = HTTPXRequest(connect_timeout=30, read_timeout=60)
    bot = ApplicationBuilder().token(api_key).request(request).build()

    # conversation handler add manga
    add_manga_conv = ConversationHandler(
        entry_points=[CommandHandler('add', tg.add)],
        states={
            AddMangaConversationStates.CHOOSE_MANGA: [MessageHandler(callback=tg.choose_manga, filters=filters.TEXT)],
            AddMangaConversationStates.GET_LAST_CHAPTER: [MessageHandler(callback=tg.get_last_chapter, filters=filters.TEXT)]
        },
        fallbacks=[CommandHandler('cancel', tg.cancel)],
    )

    manage_manga_conv = ConversationHandler(
        entry_points=[CommandHandler('list', tg.list_mangas)],
        states={
            ManageMangaConversationStates.REMOVE_MANGA: [MessageHandler(callback=tg.remove_manga, filters=filters.TEXT)]
        },
        fallbacks=[CommandHandler('cancel', tg.cancel)],
    )

    
    
    start_handler = CommandHandler('start', tg.start)
    help_handler = CommandHandler('help', tg.help)

    bot.add_handler(start_handler)
    bot.add_handler(help_handler)

    bot.add_handler(add_manga_conv)
    bot.add_handler(manage_manga_conv)

    log.info("Starting the bot...")
    bot.run_polling()

if __name__ == "__main__":
    main()