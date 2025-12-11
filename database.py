"""Database Operations Module."""
import sqlite3


class DataBase:
    """Sqlite database manager."""

    def __init__(self):
        """To create the database for the first time when the class starts."""
        self.database()

    def connection(self):
        """Create a connection object."""
        return sqlite3.connect("./results.db")

    def database(self):
        """
        Initialize the database schema.

        An index is also created for the hash column for performance.
        """
        with sqlite3.connect("./results.db") as ccon:
            command = ccon.cursor()
            command.execute(""" CREATE TABLE IF NOT EXISTS TBL_RESULTS
            (idno INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT, name TEXT, size INT, hash TEXT) """)
            command.execute(""" CREATE INDEX IF NOT EXISTS indexhash
            ON TBL_RESULTS (hash) """)
            return ccon

    def insertFile(self, path, name, size, hash):
        """
        Add a new file record to the database.

        The record consists of file's full path, name, size and SHA-256 hash.
        """
        ccon = self.database()
        command = ccon.cursor()
        command.execute(""" INSERT INTO TBL_RESULTS
        (path, name, size, hash)
        VALUES (?, ?, ?, ?)""", (path, name, size, hash))
        ccon.commit()

    def duplicates(self):
        """
        Find duplicate files in the database.

        Files with more than 1 group and a common hash were found.
        """
        ccon = self.database()
        command = ccon.cursor()
        command.execute(""" SELECT name, path, size, hash
        FROM TBL_RESULTS WHERE hash IN
        (SELECT hash FROM TBL_RESULTS GROUP BY hash HAVING COUNT(*) > 1)
        ORDER BY hash """)
        return command.fetchall()

    def clear(self):
        """Clear all browsing history in the database."""
        ccon = self.database()
        command = ccon.cursor()
        command.execute(" DELETE FROM TBL_RESULTS")
        ccon.commit()

    def delete_file(self, path):
        """Delete specified file from the database."""
        ccon = self.database()
        command = ccon.cursor()
        command.execute("DELETE FROM TBL_RESULTS WHERE path = ?", (path,))
        ccon.commit()
