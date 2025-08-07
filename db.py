import sqlite3
import logger
from scraper import Manga

log = logger.get_logger(__name__)

class MangaRepository:
    def __init__(self) -> None:
        try:

            self.connection = sqlite3.connect("database.db")
            self.cursor = self.connection.cursor()

            # table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (    
                    url TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    published_at TEXT NOT NULL
                )       
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS mangas (
                    url TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    last_chapter_url TEXT NOT NULL,
                    FOREIGN KEY (last_chapter_url) REFERENCES chapters(url)
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_mangas (
                    chat_id INTEGER,
                    manga_url TEXT,
                    FOREIGN KEY (chat_id) REFERENCES users(chat_id),
                    FOREIGN KEY (manga_url) REFERENCES mangas(url)
                )
            """)
            self.connection.commit()
            log.info("Database initialized successfully.")
        except sqlite3.Error as e:
            log.exception(f"Database error: {e}")
            raise
    
    def save_manga(chat_id: int, manga: Manga) -> None:
        """Save a manga to the database, along with its last chapter."""
        log.info("Saving manga to db")



    def find_all_mangas_by_chat_id(chat_id: int) -> list[Manga]:
        log.info(f"Fetching all mangas of the chat_id {chat_id}")
    
    

