from db import MangaRepository, UserRepository, get_connection, ChapterRepository

connection = get_connection()

# global manga repository instance
mangaRepo = MangaRepository(connection)
userRepo = UserRepository(connection)
chapterRepo = ChapterRepository(connection)