import dotenv
from telegram import ReplyKeyboardMarkup, Update
import logger as logger

from telegram.ext import ApplicationBuilder, CommandHandler
import tg
from telegram.ext import ContextTypes


log = logger.get_logger(__name__)


CHOOSE_MANGA = 1
GET_LAST_CHAPTER = 2
DOWNLOAD_OR_READ = 3

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["1", "2", "3"]]

    await update.message.reply_text(
        "Choose your manga, by inserting a number!\n",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Choose a number"
         )
    )
        





def main(): 
    api_key = dotenv.get_key(".env", "TELEGRAM_API_KEY")
    if not api_key:
        log.error("TELEGRAM_API_KEY environment variable is not set.")
        return
    
    bot = ApplicationBuilder().token(api_key).build()


    # conversation handler add manga





    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', tg.help)
    add_helper = CommandHandler('add', tg.add)

    bot.add_handler(start_handler)
    bot.add_handler(help_handler)
    bot.add_handler(add_helper)


    log.info("Starting the bot...")
    bot.run_polling()

if __name__ == "__main__":
    main()