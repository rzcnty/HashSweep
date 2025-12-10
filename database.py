
import sqlite3


class DataBase:
    def __init__(self):
        self.database()

    def connection(self):
        return sqlite3.connect("./results.db")

    def database(self):
        with sqlite3.connect("./results.db") as ccon:
            command = ccon.cursor()
            command.execute(""" CREATE TABLE IF NOT EXISTS TBL_RESULTS
            (idno INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT, name TEXT, size INT, hash TEXT) """)
            command.execute(""" CREATE INDEX IF NOT EXISTS indexhash
            ON TBL_RESULTS (hash) """)
            return ccon

    def insertFile(self, path, name, size, hash):
        ccon = self.database()
        command = ccon.cursor()
        command.execute(""" INSERT INTO TBL_RESULTS
        (path, name, size, hash)
        VALUES (?, ?, ?, ?)""", (path, name, size, hash))
        ccon.commit()

    def duplicates(self):
        ccon = self.database()
        command = ccon.cursor()
        command.execute(""" SELECT name, path, size, hash
        FROM TBL_RESULTS WHERE hash IN
        (SELECT hash FROM TBL_RESULTS GROUP BY hash HAVING COUNT(*) > 1)
        ORDER BY hash """)
        return command.fetchall()

    def clear(self):
        ccon = self.database()
        command = ccon.cursor()
        command.execute(" DELETE FROM TBL_RESULTS")
        ccon.commit()
