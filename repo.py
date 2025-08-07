from db import MangaRepository, UserRepository, get_connection

connection = get_connection()

# global manga repository instance
mangaRepo = MangaRepository(connection)
userRepo = UserRepository(connection)