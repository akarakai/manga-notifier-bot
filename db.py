import sqlite3
import logger
from scraper import Chapter, Manga


log = logger.get_logger(__name__)

def get_connection() -> sqlite3.Connection:
    return sqlite3.connect("database.db", check_same_thread=False)


class MangaRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        try:
            self.connection = connection
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
                CREATE TABLE IF NOT EXISTS user_mangas (
                    user_id INTEGER,
                    manga_url TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (manga_url) REFERENCES mangas(url)
                )
            """)
            self.connection.commit()
            log.info("Database initialized successfully.")
        except sqlite3.Error as e:
            log.exception(f"Database error: {e}")
            raise
    
    def save_manga(self, user_id: int, manga: Manga) -> None:
        """Save a manga to the database, along with its last chapter."""
        try:
            # check if manga already exist
            self.cursor.execute("SELECT * FROM mangas WHERE url = ?", (manga.url,)) # must be a tuple
            if self.cursor.fetchone():
                log.info(f"Manga {manga.title} already exists in the database.")
                # check if the manga is already associated with the user
                self.cursor.execute("SELECT * FROM user_mangas WHERE user_id = ? AND manga_url = ?", (user_id, manga.url))
                if self.cursor.fetchone():
                    log.info(f"Manga {manga.title} is already associated with user_id {user_id}. Doing nothing.")
                    return
                # add the manga to user_mangas
                self.cursor.execute("INSERT INTO user_mangas (user_id, manga_url) VALUES (?, ?)", (user_id, manga.url))
                log.info(f"Manga {manga.title} added to user_mangas for chat_id {user_id}.")
                return
            
            
            
            # manga is new in the database, save the manga, its last chapter, and associate it with the user
            self.cursor.execute("INSERT INTO mangas (url, title, last_chapter_url) VALUES (?, ?, ?)", 
                                (manga.url, manga.title, manga.last_chapter.url))
            self.cursor.execute("INSERT INTO chapters (url, title, published_at) VALUES (?, ?, ?)", 
                                (manga.last_chapter.url, manga.last_chapter.title, manga.last_chapter.published_at))
            self.cursor.execute("INSERT INTO user_mangas (user_id, manga_url) VALUES (?, ?)", (user_id, manga.url))
            self.connection.commit()
            log.info(f"Manga {manga.title} saved to the database and associated with chat_id {user_id}.")

        except sqlite3.Error as e:
            log.exception(f"Error saving manga {manga.title}: {e}")
            self.connection.rollback()
            raise

    def find_all_mangas_by_chat_id(self, user_id: int) -> list[Manga]:
        # load all mangas associated with a chat_id
        try:
            self.cursor.execute("""
                SELECT m.url, m.title, c.url, c.title, c.published_at 
                FROM user_mangas um
                JOIN mangas m ON um.manga_url = m.url
                JOIN chapters c ON m.last_chapter_url = c.url
                WHERE um.user_id = ?
            """, (user_id,))
            rows = self.cursor.fetchall()
            mangas = [
                Manga(
                    url=row[0],
                    title=row[1],
                    last_chapter=Chapter(
                        url=row[2],
                        title=row[3],
                        published_at=row[4]
                    )   
                )
                for row in rows
            ]
            log.info(f"Found {len(mangas)} mangas for user_id {user_id}.")
            return mangas
        except sqlite3.Error as e:
            log.exception(f"Error finding mangas for userid_id {user_id}: {e}")
            raise

    def find_all_mangas(self) -> list[Manga]:
        """Find all mangas in the database."""
        try:
            self.cursor.execute("""
                SELECT m.url, m.title, c.url, c.title, c.published_at 
                FROM mangas m
                JOIN chapters c ON m.last_chapter_url = c.url
            """)
            rows = self.cursor.fetchall()
            mangas = [
                Manga(
                    url=row[0],
                    title=row[1],
                    last_chapter=Chapter(
                        url=row[2],
                        title=row[3],
                        published_at=row[4]
                    )   
                )
                for row in rows
            ]
            log.info(f"Found {len(mangas)} mangas in the database.")
            return mangas
        except sqlite3.Error as e:
            log.exception(f"Error finding all mangas: {e}")
            raise
    
    def find_manga_by_chapter_url(self, chapter_url: str) -> Manga | None:
        """Find a manga by its chapter URL."""
        try:
            self.cursor.execute("""
                SELECT m.url, m.title, c.url, c.title, c.published_at 
                FROM mangas m
                JOIN chapters c ON m.last_chapter_url = c.url
                WHERE c.url = ?
            """, (chapter_url,))
            row = self.cursor.fetchone()
            if row:
                return Manga(
                    url=row[0],
                    title=row[1],
                    last_chapter=Chapter(
                        url=row[2],
                        title=row[3],
                        published_at=row[4]
                    )   
                )
            return None
        except sqlite3.Error as e:
            log.exception(f"Error finding manga by chapter URL {chapter_url}: {e}")
            raise
class UserRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        try:
            self.connection = connection
            self.cursor = self.connection.cursor()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY
                )
            """)
            self.connection.commit()

        except sqlite3.Error as e:
            log.exception(f"Database error: {e}")
            raise
    
    def save_user(self, user_id: int) -> None:
        """Save a user to the database."""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            self.connection.commit()
            log.info(f"User with user_id {user_id} saved to the database.")
        except sqlite3.Error as e:
            log.exception(f"Error saving user with user_id {user_id}: {e}")
            self.connection.rollback()
            raise
    
    def find_all_user_ids(self) -> list[int]:
        """Find all user IDs in the database."""
        try:
            self.cursor.execute("SELECT user_id FROM users")
            rows = self.cursor.fetchall()
            user_ids = [row[0] for row in rows]
            log.info(f"Found {len(user_ids)} user IDs in the database.")
            return user_ids
        except sqlite3.Error as e:
            log.exception(f"Error finding user IDs: {e}")
            raise
    def find_user_ids_by_manga_url(self, manga_url: str) -> list[int]:
        """Find all user IDs associated with a manga URL."""
        try:
            self.cursor.execute("SELECT user_id FROM user_mangas WHERE manga_url = ?", (manga_url,))
            rows = self.cursor.fetchall()
            user_ids = [row[0] for row in rows]
            log.info(f"Found {len(user_ids)} user IDs for manga URL {manga_url}.")
            return user_ids
        except sqlite3.Error as e:
            log.exception(f"Error finding user IDs for manga URL {manga_url}: {e}")
            raise

    def delete_manga_of_user(self, user_id: int, manga_url: str) -> None:
        """Delete a manga of a user from the database."""
        try:
            self.cursor.execute("DELETE FROM user_mangas WHERE user_id = ? AND manga_url = ?", (user_id, manga_url))
            self.connection.commit()
            log.info(f"Manga deleted for user_id {user_id}.")
        except sqlite3.Error as e:
            log.exception(f"Error deleting manga for user_id {user_id}: {e}")
            self.connection.rollback()
            raise

class ChapterRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.cursor = self.connection.cursor()
    
    def find_chapter(self, chapter_url: str) -> Chapter | None:
        """Find a chapter by its URL."""
        try:
            self.cursor.execute("SELECT * FROM chapters WHERE url = ?", (chapter_url,))
            row = self.cursor.fetchone()
            if row:
                return Chapter(
                    url=row[0],
                    title=row[1],
                    published_at=row[2]
                )
            return None
        except sqlite3.Error as e:
            log.exception(f"Error finding chapter with URL {chapter_url}: {e}")
            raise
        