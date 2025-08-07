from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
from enum import Enum, auto

import logger as logger
from scraper import Chapter, MangaScraper, Manga
import downloader
from downloader import download_pdf 
from repo import mangaRepo, userRepo, chapterRepo
from sqlite3 import Error as DbError

log = logger.get_logger(__name__)


class AddMangaConversationStates(Enum):
    CHOOSE_MANGA = auto()
    GET_LAST_CHAPTER = auto()

class ManageMangaConversationStates(Enum):
    LIST_MANGAS = auto()
    CHOOSE_MANGA = auto()
    REMOVE_MANGA = auto()


# ====== COMMAND HANDLERS ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    log.info(f"/start from {update.effective_user.name} ({user_id})")
    userRepo.save_user(user_id)
    await help(update, context)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info(f"/help from {update.effective_user.name} ({update.effective_user.id})")
    await update.message.reply_text(
        "Welcome to the Manga Notifier Bot.\n\n"
        "Available commands:\n"
        "/help - Show this message\n"
        "/add <manga_title> - Add a manga to your list\n"
        "/list - List your mangas. You can remove the chosen manga\n"
        "/download <chapter_url> - Download the requested chapter. Only WeebCentral urls are accepted \n"
        "/cancel - Cancel the current operation\n"
    )

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download a chapter from WeebCentral."""
    log.info(f"/download from {update.effective_user.name} ({update.effective_user.id})")
    chapter_url = " ".join(context.args)
    print(chapter_url)
    if not chapter_url:
        await update.message.reply_text("Please provide a chapter URL to download.")
        return
    if not chapter_url.startswith("https://weebcentral.com/chapters"):
        await update.message.reply_text("Invalid URL. Please provide a valid WeebCentral chapter URL.")
        return
    try:
        scraper = MangaScraper()

        chapter = chapterRepo.find_chapter(chapter_url)
        manga_title, chapter_title = None, None
        if not chapter:
            # you have to scrape this chapter
            manga_title, chapter_title = scraper.get_data_from_chapter_url(chapter_url)

        # TODO change
        img_urls = scraper.get_chapter_image_urls(Chapter(
            "NO TITLE",
            chapter_url,
            "NO DATETIME"
        ))
        img_bytes = download_pdf(img_urls)
        await update.message.reply_document(
            document=img_bytes,
            filename=f"{manga_title} - {chapter_title}.pdf",
            reply_markup=ReplyKeyboardRemove()
        )
        log.info(f"Chapter {chapter_title} from the Manga {manga_title} was successfully downloaded")
    except Exception as e:
        log.error(f"Error downloading chapter: {e}")
        await update.message.reply_text("An error occurred while downloading the chapter.")
        return
    finally:
        scraper.close()



# ====== ADD MANGA CONVERSATION ======
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> AddMangaConversationStates | None:
    log.info(f"/add from {update.effective_user.name} ({update.effective_user.id})")

    if not context.args:
        await update.message.reply_text("Please provide a manga title to search for.")
        return

    query = " ".join(context.args)
    scraper = MangaScraper()

    try:
        scraper.go_to_homepage()
        mangas = scraper.get_queried_mangas(query)

        if not mangas:
            await update.message.reply_text("No mangas found for your query.")
            return

        context.user_data['mangas'] = mangas

        await update.message.reply_text(
            "Choose your manga:",
            reply_markup=ReplyKeyboardMarkup(
                [[manga.title] for manga in mangas],
                one_time_keyboard=True,
                input_field_placeholder="Choose a manga"
            )
        )
        return AddMangaConversationStates.CHOOSE_MANGA

    except Exception as e:
        log.error(f"Error in /add: {e}")
        await update.message.reply_text("An error occurred while processing your request.")
    finally:
        scraper.close()

async def choose_manga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> AddMangaConversationStates | None:
    user_input = update.message.text.strip()
    mangas: list[Manga] = context.user_data.get("mangas", [])

    if not mangas:
        await update.message.reply_text("No mangas available to choose from.")
        return

    selected_manga = next((m for m in mangas if m.title == user_input), None)

    if not selected_manga:
        await update.message.reply_text("Invalid choice. Please choose a valid manga.")
        return

    context.user_data['chosen_manga'] = selected_manga
    log.info(f"Manga selected: {selected_manga.title}")
    await update.message.reply_text(f"You selected: {selected_manga.title}")

    scraper = MangaScraper()
    try:
        scraper.go_to_homepage()
        last_chapter = scraper.get_last_chapter(selected_manga)

        if not last_chapter:
            await update.message.reply_text("Could not retrieve the last chapter.")
            return

        context.user_data['last_chapter'] = last_chapter
        await update.message.reply_text(
            f"Last chapter: {last_chapter.title}\nPublished at: {last_chapter.published_at}"
        )

        await update.message.reply_text(
            "What would you like to do?",
            reply_markup=ReplyKeyboardMarkup(
                [["Download", "Read Online", "Do Nothing"]],
                one_time_keyboard=True,
                input_field_placeholder="Choose an option"
            )
        )

        # Save manga to the database
        chat_id = update.effective_user.id
        mangaRepo.save_manga(chat_id, selected_manga)

        return AddMangaConversationStates.GET_LAST_CHAPTER

    except Exception as e:
        log.error(f"Error retrieving last chapter: {e}")
        await update.message.reply_text("An error occurred while retrieving the last chapter.")
    except DbError as e:
        await update.message.reply_text("An error occurred while saving the manga to the database.\nYou will not be notified about new chapters.")    
    finally:
        scraper.close()

async def get_last_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    CHOICES = ["Download", "Read Online", "Do Nothing"]
    choice = update.message.text.strip()

    if choice not in CHOICES:
        await update.message.reply_text(
            "Invalid choice. Please choose a valid option.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    manga: Manga = context.user_data.get('chosen_manga')
    chapter: Chapter = context.user_data.get('last_chapter')

    if not manga or not chapter:
        await update.message.reply_text(
            "No manga or chapter info available. Please try again.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    if choice == "Download":
        await update.message.reply_text("Downloading the last chapter...")
        scraper = MangaScraper()
        try:
            image_urls = scraper.get_chapter_image_urls(chapter)
        finally:
            scraper.close()

        if not image_urls:
            await update.message.reply_text("No images found for the chapter.")
            context.user_data.clear()
            return ConversationHandler.END

        pdf = downloader.download_pdf(image_urls)
        await update.message.reply_document(
            document=pdf,
            filename=f"{manga.title} - {chapter.title}.pdf",
            reply_markup=ReplyKeyboardRemove()
        )
        log.info(f"Sent PDF for {manga.title} - {chapter.title}")

    elif choice == "Read Online":
        await update.message.reply_text(chapter.url, reply_markup=ReplyKeyboardRemove())

    elif choice == "Do Nothing":
        await update.message.reply_text(
            "You'll be notified when a new chapter is available on WeebCentral.",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END

# ====== MANAGE MANGE CONVERSATION ======
async def list_mangas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ManageMangaConversationStates | None:
    """List all mangas associated with the user and allow them to choose one to remove."""
    chat_id = update.effective_user.id
    mangas = mangaRepo.find_all_mangas_by_chat_id(chat_id)

    if not mangas:
        await update.message.reply_text(
            "You have no mangas in your list.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # add mangas to user data for later use
    context.user_data['mangas'] = mangas

    await update.message.reply_text(
        "Choose the manga which you want to remove.",
        reply_markup=ReplyKeyboardMarkup(
            [[manga.title] for manga in mangas],
            one_time_keyboard=True,
            input_field_placeholder="Choose a manga to remove"
        )
    )
    return ManageMangaConversationStates.REMOVE_MANGA

async def remove_manga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ManageMangaConversationStates | int | None:
    """Remove the selected manga from the user's list."""
    user_input = update.message.text.strip()
    chat_id = update.effective_user.id
    mangas: list[Manga] = context.user_data.get("mangas", [])

    if not mangas:
        await update.message.reply_text("No mangas available to remove.")
        return

    selected_manga = next((m for m in mangas if m.title == user_input), None)

    if not selected_manga:
        await update.message.reply_text("Invalid choice. Please choose a valid manga.")
        return

    try:
        userRepo.delete_manga_of_user(chat_id, selected_manga.url)
        await update.message.reply_text(f"{selected_manga.title} has been removed from your list.")
    except DbError as e:
        log.error(f"Error removing manga: {e}")
        await update.message.reply_text("An error occurred while removing the manga.")

    context.user_data.clear()
    return ConversationHandler.END



async def notifier(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Notify all users about new chapters for their subscribed mangas."""
    log.info("Running notifier job...")
    scraper = MangaScraper()
    # get all mangas from the database
    mangas = mangaRepo.find_all_mangas()
    
    try:
        for manga in mangas:
            scraped_last_chapter = scraper.get_last_chapter(manga)
            if scraped_last_chapter.url != manga.last_chapter.url:
                log.info(f"New chapter found for {manga.title}: {scraped_last_chapter.title}")
                manga.add_chapter(scraped_last_chapter)
                # notify all users subscribed to this manga
                user_ids = userRepo.find_user_ids_by_manga_url(manga.url)
                for user_id in user_ids:
                    context.bot.send_message(
                        user_id=user_id,
                        text=f"{scraped_last_chapter.url}\n"
                    )

    except Exception as e:
        log.error(f"Error in notifier: {e}")
        return
    finally:
        scraper.close()
    




async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
            "You'll be notified when a new chapter is available on WeebCentral.",
            reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END
