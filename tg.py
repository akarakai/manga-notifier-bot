from telegram import ReplyKeyboardMarkup, Update
import logger as logger
from telegram.ext import ContextTypes
from scraper import MangaScraper

log = logger.get_logger(__name__)



async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info(f"Received /help command from {update.effective_user.name} with ID {update.effective_user.id}")
    text = (
        "Welcome to the Manga Notifier Bot.\n"
        "Here are the commands you can use:\n"
        "/help - Show this help message\n"
        "/add <manga_title> - Add a manga to your list\n"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Add a manga to the user's list """
    log.info(f"Received /add command from {update.effective_user.name} with ID {update.effective_user.id}")
    scraper = MangaScraper()
    try:
        if len(context.args) == 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please provide a manga title to search for."
            )
            return
        
        query = " ".join(context.args)
        scraper.go_to_homepage()
        mangas = scraper.get_queried_mangas(query)
        
        if not mangas:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No mangas found for your query."
            )
            return
        
        manga_list = [f"{manga.title}" for manga in mangas]        
        await update.message.reply_text(    
            f"Choose your manga",
            reply_markup=ReplyKeyboardMarkup(
                [[manga] for manga in manga_list], one_time_keyboard=True, input_field_placeholder="Choose a manga"
        ))
    

    except Exception as e:
        log.error(f"Error while processing /add command: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An error occurred while processing your request."
        )
    finally:
        scraper.driver.quit()
        log.info("MangaScraper closed.")


