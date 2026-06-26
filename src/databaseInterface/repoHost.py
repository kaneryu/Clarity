from src.databaseInterface import dbcore as dbCore
from src.databaseInterface.Repositories import SongRepository, ListenRepository

dbCore.initializeDatabase()
globalDbInterface = dbCore.DatabaseInterface()
songRepository = SongRepository(globalDbInterface)
listenRepository = ListenRepository(globalDbInterface)
