"""Main Application Module."""
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                             QMessageBox, QTableWidgetItem, QHeaderView)
from Widget import Ui_Form
from database import DataBase
from scanner import Scanner


class Form(QMainWindow):
    """Main Window Class."""

    def __init__(self):
        """Launch the application window."""
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle("HashSweep")

        # Some GUI settings
        header = self.ui.tbl_results.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.ui.tbl_results.setColumnHidden(3, True)

        # Button click events
        self.ui.btn_browse.clicked.connect(self.select_folder)
        self.ui.btn_start.clicked.connect(self.start_scan)
        self.ui.btn_delete.clicked.connect(self.delete_selected)
        self.ui.btn_hash.toggled.connect(self.toggle_hash_view)

        self.db = DataBase()
        self.worker = None

    def select_folder(self):
        """Make user choose a folder."""
        folder = QFileDialog.getExistingDirectory(self,
                                                  """Taranacak Klasörü Seç""")
        if folder:
            self.ui.txt_path.setText(folder)
            self.ui.lbl_status.setText("Hazır.")
            self.ui.lbl_stats.setText("Henüz tarama yapılmadı.")

    def start_scan(self):
        """Start the scanning process."""
        folder_path = self.ui.txt_path.text()

        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Uyarı",
                                """Lütfen geçerli bir klasör seçin!""")
            return

        self.ui.btn_start.setEnabled(False)
        self.ui.btn_delete.setEnabled(False)
        self.ui.tbl_results.setRowCount(0)
        self.ui.progress_bar.setValue(0)

        self.worker = Scanner(folder_path)

        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.ui.lbl_status.setText)
        self.worker.finished_signal.connect(self.scan_finished)

        self.worker.start()

    def update_progress(self, val):
        """Write the percentage from scanner to bar."""
        self.ui.progress_bar.setValue(val)

    def scan_finished(self):
        """When scan is finished."""
        self.ui.btn_start.setEnabled(True)
        self.ui.btn_delete.setEnabled(True)
        self.ui.lbl_status.setText("Tarama Tamamlandı. Kopyalar aranıyor...")

        duplicates = self.db.duplicates()
        self.populate_table(duplicates)

    def populate_table(self, data):
        """Fill the data from the database into the table."""
        self.ui.tbl_results.clearContents()

        COLUMNS = ["Dosya Adı", "Konum", "Boyut", "Hash"]
        self.ui.tbl_results.setHorizontalHeaderLabels(COLUMNS)

        if data:
            self.ui.tbl_results.setRowCount(len(data))

            rowno = 0

            for row_data in data:
                for columnno in range(len(COLUMNS)):
                    item_text = str(row_data[columnno])

                    if columnno == 2:
                        item_text += " bytes"

                    self.ui.tbl_results.setItem(rowno, columnno,
                                                QTableWidgetItem(item_text))
                rowno += 1

            count = len(data)
            self.ui.lbl_stats.setText(f"{count} adet kopya dosya bulundu.")
            self.ui.lbl_status.setText("Analiz Bitti.")

        else:
            self.ui.tbl_results.setRowCount(0)
            self.ui.lbl_status.setText("Harika! Hiç kopya dosya bulunamadı.")

    def toggle_hash_view(self, checked):
        """Show/hide hash column."""
        self.ui.tbl_results.setColumnHidden(3, not checked)

    def delete_selected(self):
        """Delete the selected file from disk and DB."""
        selected_rows = self.ui.tbl_results.selectionModel().selectedRows()
        if not selected_rows:
            return

        reply = QMessageBox.question(self, "Silme Onayı",
                                     f"""{len(selected_rows)} dosyayı
                                     kalıcı olarak silmek istiyor musun?""")

        if reply == QMessageBox.StandardButton.Yes:
            for index in sorted(selected_rows, reverse=True):
                file_path = self.ui.tbl_results.item(index.row(), 1).text()

                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)

                    self.db.delete_file(file_path)

                    self.ui.tbl_results.removeRow(index.row())

                except Exception as error:
                    QMessageBox.critical(self, "Hata", f"Silinemedi: {error}")


if __name__ == "__main__":
    app = QApplication([])
    window = Form()
    window.show()
    app.exec()
