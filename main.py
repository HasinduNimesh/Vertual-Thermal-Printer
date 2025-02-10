import sys
import os
import time
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLabel,
    QWidget,
    QPushButton,
    QToolBar,
    QFileDialog,
    QMessageBox
)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# -------------------------------
# Thermal Printer Simulation Dialog
# -------------------------------
class ThermalPrinterSimulator(QDialog):
    def __init__(self, print_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thermal Print Simulation")
        self.resize(400, 600)
        
        main_layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Thermal Print Preview", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(self.title_label)
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Courier New", 10))
        self.text_edit.setText(print_text)
        main_layout.addWidget(self.text_edit)
        
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Output")
        self.save_button.clicked.connect(self.save_output)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

    def save_output(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "Saved", "Output saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

# -------------------------------
# File System Event Handler
# -------------------------------
class PrintMonitorHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".txt"):
            with open(event.src_path, "r", encoding="utf-8") as f:
                data = f.read()
            dialog = ThermalPrinterSimulator(data)
            dialog.exec()

# -------------------------------
# Main Application Window
# -------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermal Printer Monitor")
        self.resize(800, 600)
        
        # Add a toolbar with actions
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        open_action = QAction("Open Directory", self)
        open_action.triggered.connect(self.open_directory)
        toolbar.addAction(open_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)

        # Central widget: instructions and status
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        self.status_label = QLabel("Choose a directory to monitor")
        layout.addWidget(self.status_label)
        self.setCentralWidget(central_widget)

        # Watchdog observer
        self.observer = None
        self.directory_to_watch = None

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.directory_to_watch = directory
            self.status_label.setText(f"Monitoring: {directory}")
            
            if self.observer:
                self.observer.stop()
                self.observer.join()

            self.observer = Observer()
            self.handler = PrintMonitorHandler()
            self.observer.schedule(self.handler, self.directory_to_watch, recursive=False)
            self.observer.start()

    def show_about(self):
        QMessageBox.information(self, "About", "Enhanced Thermal Printer Simulation with UI improvements.")

    def closeEvent(self, event):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        event.accept()

# -------------------------------
# Main Entry
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())