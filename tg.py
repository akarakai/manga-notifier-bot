from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
from enum import Enum, auto

import logger as logger
from scraper import Chapter, MangaScraper, Manga
import downloader
from dataclasses import dataclass

log = logger.get_logger(__name__)

@dataclass
class UserManga:
    chat_id: int
    mangas: list[Manga]


class ConversationStates(Enum):
    CHOOSE_MANGA = auto()
    GET_LAST_CHAPTER = auto()


# ====== COMMAND HANDLERS ======

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info(f"/help from {update.effective_user.name} ({update.effective_user.id})")
    await update.message.reply_text(
        "Welcome to the Manga Notifier Bot.\n\n"
        "Available commands:\n"
        "/help - Show this message\n"
        "/add <manga_title> - Add a manga to your list"
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationStates | None:
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
        return ConversationStates.CHOOSE_MANGA

    except Exception as e:
        log.error(f"Error in /add: {e}")
        await update.message.reply_text("An error occurred while processing your request.")
    finally:
        scraper.close()


# ====== CONVERSATION HANDLERS ======

async def choose_manga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationStates | None:
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
        return ConversationStates.GET_LAST_CHAPTER

    except Exception as e:
        log.error(f"Error retrieving last chapter: {e}")
        await update.message.reply_text("An error occurred while retrieving the last chapter.")
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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
            "You'll be notified when a new chapter is available on WeebCentral.",
            reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END
