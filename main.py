
from PyQt6.QtWidgets import QMainWindow #, QApplication
# from PyQt6.QtCore import Qt
# from PyQt6.QtGui import QIcon
from Widget import Ui_Form
import sqlite3


class Form(QMainWindow):
    def __init__(self):
        super().__init__()
        self.form = Ui_Form()
        self.form.setupUi(self)

        # Definitions

        # Button typing operations

    def database(self):
        with sqlite3.connect("./users.db") as ccon:
            command = ccon.cursor()
            command.execute(""" CREATE TABLE IF NOT EXISTS TBL_RESULS
            (idno INT PRIMARY KEY AUTOINCREMENT,
            path TEXT, name TEXT, size INT, hash TEXT) """)
            return ccon
