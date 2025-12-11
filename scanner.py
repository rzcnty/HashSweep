"""File Scanning and Hashing Module."""
import os
import hashlib
from PyQt6.QtCore import QThread, pyqtSignal
from database import DataBase


class Scanner(QThread):
    """
    The Qthread class ensures that the interface works without freezing.

    Signals were defined for communication with the GUI.
    """

    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, folder_path):
        """File path is made available to the entire class."""
        super().__init__()
        self.folder_path = folder_path
        self.is_running = True

    def run(self):
        """
        First function that will run when the thread starts.

        Will start with start()
        """
        self.status_signal.emit("Dosyalar listeleniyor...")
        file_list = []
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                file_list.append(os.path.join(root, file))

        total_files = len(file_list)
        if total_files == 0:
            self.status_signal.emit("Klasör boş!")
            self.finished_signal.emit()
            return

        db = DataBase()
        db.clear()

        processed_count = 0
        for file_path in file_list:
            if not self.is_running:
                break

            file_name = os.path.basename(file_path)
            self.status_signal.emit(f"Taranıyor: {file_name}")

            try:
                file_size = os.path.getsize(file_path)
                file_hash = self.calculate_hash(file_path)
                db.insertFile(file_path, file_name, file_size, file_hash)

            except Exception as error:
                print(f"HATA: ({file_name}): {error}")

            processed_count += 1
            percent = int((processed_count / total_files) * 100)
            self.progress_signal.emit(percent)

        self.status_signal.emit("Tarama Tamamlandı!")
        self.finished_signal.emit()

    def calculate_hash(self, file_path, block_size=65536):
        """
        Block-by-block reading to read large files without bloating RAM.

        block_size = 64KB
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        except PermissionError:
            return "ACCESS_DENIED"
        except Exception:
            return "ERROR"

    def stop(self):
        """To stop the thread."""
        self.is_running = False
