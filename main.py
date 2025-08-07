from datetime import time, timedelta
import dotenv
import logging as log
import pytz
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
import tg
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
    return os.path.join(base_path, relative_path)

def main():
    api_key = dotenv.get_key(resource_path(".env"), "TELEGRAM_API_KEY")
    if not api_key:
        log.error("TELEGRAM_API_KEY environment variable is not set.")
        return
    
    request = HTTPXRequest(connect_timeout=30, read_timeout=60)
    bot = ApplicationBuilder().token(api_key).request(request).build()

    # conversation handler add manga
    add_manga_conv = ConversationHandler(
        entry_points=[CommandHandler('add', tg.add)],
        states={
            tg.AddMangaConversationStates.CHOOSE_MANGA: [MessageHandler(callback=tg.choose_manga, filters=filters.TEXT)],
            tg.AddMangaConversationStates.GET_LAST_CHAPTER: [MessageHandler(callback=tg.get_last_chapter, filters=filters.TEXT)]
        },
        fallbacks=[CommandHandler('cancel', tg.cancel)],
    )

    manage_manga_conv = ConversationHandler(
        entry_points=[CommandHandler('list', tg.list_mangas)],
        states={
            tg.ManageMangaConversationStates.REMOVE_MANGA: [MessageHandler(callback=tg.remove_manga, filters=filters.TEXT)]
        },
        fallbacks=[CommandHandler('cancel', tg.cancel)],
    )

    start_handler = CommandHandler('start', tg.start)
    help_handler = CommandHandler('help', tg.help)
    download_handler = CommandHandler("download", tg.download)

    bot.add_handler(start_handler)
    bot.add_handler(help_handler)

    bot.add_handler(add_manga_conv)
    bot.add_handler(manage_manga_conv)
    bot.add_handler(download_handler)

    log.info("Starting the bot...")

    # add notifier
    # brussels_time = time(hour=13, minute=30, tzinfo=pytz.timezone('Europe/Brussels'))
    # bot.job_queue.run_daily(tg.notifier, time=brussels_time)
    bot.job_queue.run_repeating(tg.notifier, interval=3600, first=timedelta(minutes=10))

    bot.run_polling()

if __name__ == "__main__":
    main()
