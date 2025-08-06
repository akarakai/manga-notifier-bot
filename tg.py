from telegram import ReplyKeyboardMarkup, Update
import logger as logger
from telegram.ext import ContextTypes
from scraper import Chapter, MangaScraper
from enum import Enum, auto
from scraper import Manga
import downloader

log = logger.get_logger(__name__)

class ConversationStates(Enum):
    CHOOSE_MANGA = auto()
    GET_LAST_CHAPTER = auto()



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



# Conversation

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationStates:
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
        
        # add mangas to the context, in order to use later
        context.user_data['mangas'] = mangas
        
        manga_list = [f"{manga.title}" for manga in mangas]        
        await update.message.reply_text(    
            f"Choose your manga",
            reply_markup=ReplyKeyboardMarkup(
                [[manga] for manga in manga_list], one_time_keyboard=True, input_field_placeholder="Choose a manga"
        ))
        return ConversationStates.CHOOSE_MANGA
    

    # TODO what to do if error?
    except Exception as e:
        log.error(f"Error while processing /add command: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An error occurred while processing your request."
        )
    finally:
        scraper.driver.quit()
        log.info("MangaScraper closed.")


async def choose_manga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationStates: # for now None
    user_choice = update.message.text.strip()
    mangas: list[Manga] = context.user_data.get("mangas", [])
    if not mangas:
        await update.message.reply_text("No mangas available to choose from.")
        return
    
    chosen_manga = next((m for m in mangas if m.title == user_choice), None)
    if not chosen_manga:
        await update.message.reply_text("Invalid choice. Please choose a valid manga.")
        return
    
    # add chosen manga to context
    context.user_data['chosen_manga'] = chosen_manga

    log.info(f"User selected manga: {chosen_manga.title}")
    await update.message.reply_text(f"You selected: {chosen_manga.title}")
    
    # get last chapter 
    scraper = MangaScraper()
    try:
        scraper.go_to_homepage()
        last_chapter = scraper.get_last_chapter(chosen_manga)
        
        if not last_chapter:
            await update.message.reply_text("Could not retrieve the last chapter.")

        # save last chapter in context
        context.user_data['last_chapter'] = last_chapter
            
        await update.message.reply_text(
            f"Last chapter: {last_chapter.title}\nPublished at: {last_chapter.published_at}"
        )

        await update.message.reply_text(
            "Would you like to download it, read it online or do nothing?",
            reply_markup=ReplyKeyboardMarkup(
                [["Download", "Read Online", "Do Nothing"]],
                one_time_keyboard=True,
                input_field_placeholder="Choose an option"
            )
        )
        return ConversationStates.GET_LAST_CHAPTER
        
    except Exception as e:
        log.error(f"Error while retrieving last chapter: {e}")
        await update.message.reply_text("An error occurred while retrieving the last chapter.")
    finally:
        scraper.driver.quit()
        log.info("MangaScraper closed.")
    
async def get_last_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    choices = ["Download", "Read Online", "Do Nothing"] # global?
    
    user_choice = update.message.text.strip()
    log.info(f"User choice for last chapter: {user_choice}")

    if user_choice not in choices:
        await update.message.reply_text("Invalid choice. Please choose a valid option.")
        return
    
    last_chapter: Chapter = context.user_data.get('last_chapter', None)
    choose_manga: Manga = context.user_data.get('chosen_manga', None)

    if not last_chapter or not choose_manga:
        await update.message.reply_text("No last chapter available. Please choose a manga first.")
        return

    if user_choice == "Download":
        # TODO Implement download logic here
        await update.message.reply_text("Downloading the last chapter...")
        # get the urls of the images
        scraper = MangaScraper()
        urls = scraper.get_chapter_image_urls(last_chapter)
        scraper.close()
        if not urls:
            await update.message.reply_text("No images found for the last chapter.")
            return
        pdf = downloader.download_pdf(urls)

    
        await update.message.reply_document(
            document=pdf,
            filename=f"{choose_manga.title} - {last_chapter.title}.pdf",
        )
        
        log.info("PDF sent successfully.")
        return
    
    elif user_choice == "Read Online":
        await update.message.reply_text(f"{last_chapter.url}")
        return
    
    elif user_choice == "Do Nothing":
        await update.message.reply_text("You will get a notification as soon as a new chapter is available in WeebCentral.")
        return
    

