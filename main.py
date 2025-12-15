"""Main Application Module."""
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog,
                             QMessageBox, QTableWidgetItem, QHeaderView,
                             QTreeWidgetItem, QAbstractItemView)
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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 250)
        self.ui.tbl_results.setColumnHidden(1, True)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 100)
        self.ui.treeWidget.header().setSectionResizeMode(0, QHeaderView.
                                                         ResizeMode.
                                                         ResizeToContents)
        self.ui.treeWidget.header().setSectionResizeMode(1, QHeaderView.
                                                         ResizeMode.
                                                         Stretch)
        self.ui.treeWidget.header().setSectionResizeMode(2, QHeaderView.
                                                         ResizeMode.
                                                         Fixed)
        self.ui.treeWidget.header().resizeSection(2, 100)

        # Button click events
        self.ui.btn_browse.clicked.connect(self.select_folder)
        self.ui.btn_start.clicked.connect(self.start_scan)
        self.ui.btn_delete.clicked.connect(self.delete_selected)
        self.ui.btn_hash.toggled.connect(self.toggle_hash_view)
        self.ui.rbtn_listwidget.toggled.connect(self.change_view)
        self.ui.rbtn_treewidget.toggled.connect(self.change_view)

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
        self.ui.progressBar.setValue(0)

        self.worker = Scanner(folder_path)

        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.ui.lbl_status.setText)
        self.worker.finished_signal.connect(self.scan_finished)

        self.worker.start()

    def update_progress(self, val):
        """Write the percentage from scanner to bar."""
        self.ui.progressBar.setValue(val)

    def scan_finished(self):
        """When scan is finished."""
        self.ui.btn_start.setEnabled(True)
        self.ui.btn_delete.setEnabled(True)
        self.ui.lbl_status.setText("Tarama Tamamlandı. Kopyalar aranıyor...")

        duplicates = self.db.duplicates()
        self.populate_table(duplicates)
        self.populate_tree(duplicates)

        if self.ui.rbtn_listwidget.isChecked():
            self.ui.stackedWidget.setCurrentIndex(0)
        else:
            self.ui.stackedWidget.setCurrentIndex(1)

    def populate_table(self, data):
        """Fill the data from the database into the table."""
        self.ui.tbl_results.clearContents()

        COLUMNS = ["Dosya Adı", "Hash", "Konum", "Boyut"]
        self.ui.tbl_results.setHorizontalHeaderLabels(COLUMNS)

        if data:
            self.ui.tbl_results.setRowCount(len(data))

            rowno = 0

            for row_data in data:
                for columnno in range(len(COLUMNS)):
                    item_txt = str(row_data[columnno])

                    if columnno == 3:
                        item_txt = self.human_readable_size(row_data[columnno])

                    self.ui.tbl_results.setItem(rowno, columnno,
                                                QTableWidgetItem(item_txt))
                rowno += 1

            count = len(data)
            self.ui.lbl_stats.setText(f"{count} adet kopya dosya bulundu.")
            self.ui.lbl_status.setText("Analiz Bitti.")

        else:
            self.ui.tbl_results.setRowCount(0)
            self.ui.lbl_status.setText("Harika! Hiç kopya dosya bulunamadı.")

    def populate_tree(self, data):
        """Fill the data from the database into the table."""
        self.ui.treeWidget.clear()

        if not data:
            return

        hash_groups = {}
        for item in data:
            # item: (name, hash, path, size)
            file_name = item[0]
            file_hash = item[1]
            file_path = item[2]
            file_size = item[3]

            if file_hash not in hash_groups:
                hash_groups[file_hash] = []
            hash_groups[file_hash].append((file_name, file_path, file_size))

        for hash_code, files_in_group in hash_groups.items():
            parent_item = QTreeWidgetItem(self.ui.treeWidget)

            total_size_bytes = 0
            for f in files_in_group:
                file_size = f[2]
                total_size_bytes = total_size_bytes + file_size

            s = f"Hash: {hash_code} ({len(files_in_group)} Dosya)"
            parent_item.setText(0, f"{s}")
            parent_item.setText(1, "")
            parent_size_str = self.human_readable_size(total_size_bytes)
            parent_item.setText(2, parent_size_str)

            for file_name, file_path, file_size in files_in_group:
                child_item = QTreeWidgetItem(parent_item)
                child_item.setText(0, file_name)
                child_item.setText(1, file_path)
                child_size_str = self.human_readable_size(file_size)
                child_item.setText(2, child_size_str)

            parent_item.setExpanded(False)

    def toggle_hash_view(self, checked):
        """Show/hide hash column."""
        self.ui.tbl_results.setColumnHidden(1, not checked)

    def get_selected_paths(self):
        """Return the selected file paths from the active view."""
        paths = []

        if self.ui.rbtn_listwidget.isChecked():
            rows = self.ui.tbl_results.selectionModel().selectedRows()
            for index in rows:
                paths.append(self.ui.tbl_results.item(index.row(), 2).text())
        else:
            items = self.ui.treeWidget.selectedItems()
            for item in items:
                if item.parent():
                    paths.append(item.text(1))
                else:
                    for i in range(item.childCount()):
                        paths.append(item.child(i).text(1))

        return list(set(paths))

    def perform_deletion(self, paths):
        """Delete the given list of files from disk and DB."""
        deleted_count = 0
        try:
            for file_path in paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
                self.db.delete_file(file_path)
                deleted_count += 1
        except Exception as error:
            QMessageBox.critical(self, "Hata", f"Silinemedi: {error}")

        return deleted_count

    def delete_selected(self):
        """Manage the process of deleting selected files."""
        paths_to_delete = self.get_selected_paths()
        if not paths_to_delete:
            return

        quest = "Dosyayı kalıcı olarak silmek istiyor musun?"
        reply = QMessageBox.question(self, "Silme Onayı",
                                     f"{len(paths_to_delete)} {quest}")

        if reply == QMessageBox.StandardButton.No:
            return

        deleted_count = self.perform_deletion(paths_to_delete)

        if deleted_count > 0:
            self.ui.lbl_status.setText(f"{deleted_count} dosya silindi.")
            new_data = self.db.duplicates()
            self.populate_table(new_data)
            self.populate_tree(new_data)
            self.ui.btn_delete.setEnabled(True)

    def change_view(self):
        """UI change according to radio buttons."""
        is_table_view = self.ui.rbtn_listwidget.isChecked()
        if is_table_view:
            self.ui.stackedWidget.setCurrentIndex(0)
        else:
            self.ui.stackedWidget.setCurrentIndex(1)

        self.ui.btn_hash.setEnabled(is_table_view)

    def human_readable_size(self, size_in_bytes):
        """Convert the size in bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                roundednum = round(size_in_bytes, 2)
                return str(roundednum) + " " + unit
            size_in_bytes /= 1024.0

        roundednum = round(size_in_bytes, 2)
        return str(roundednum) + " TB"


if __name__ == "__main__":
    app = QApplication([])
    window = Form()
    window.show()
    app.exec()
