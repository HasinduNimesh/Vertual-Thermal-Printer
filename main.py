import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QLabel,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont
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
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        # Use a fixed-width (monospace) font to mimic a thermal printer
        self.text_edit.setFont(QFont("Courier New", 10))
        self.text_edit.setText(print_text)
        layout.addWidget(self.text_edit)

# -------------------------------
# File System Event Handler
# -------------------------------
class MyFileEventHandler(FileSystemEventHandler):
    """
    A watchdog event handler that reads new files and emits their content.
    """
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def on_created(self, event):
        # Only process if the event is a file creation (not a directory)
        if not event.is_directory:
            try:
                # Read the file content (assuming UTF-8 encoding)
                with open(event.src_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Emit the content using the provided signal
                self.signal.emit(content)
                # Optionally, remove the file after reading it
                os.remove(event.src_path)
            except Exception as e:
                print("Error reading file:", e)

# -------------------------------
# QThread to Watch a Directory
# -------------------------------
class PrintFileWatcher(QThread):
    # This signal will be emitted when a new print file is detected;
    # the content (a string) is passed along.
    fileDetected = pyqtSignal(str)

    def __init__(self, directory, parent=None):
        super().__init__(parent)
        self.directory = directory
        self.observer = Observer()
        self._running = True

    def run(self):
        event_handler = MyFileEventHandler(self.fileDetected)
        self.observer.schedule(event_handler, self.directory, recursive=False)
        self.observer.start()
        try:
            while self._running:
                time.sleep(1)
        except Exception as e:
            print("Exception in file watcher:", e)
        self.observer.stop()
        self.observer.join()

    def stop(self):
        self._running = False
        self.wait()

# -------------------------------
# Main Window
# -------------------------------
class MainWindow(QMainWindow):
    def __init__(self, watch_directory):
        super().__init__()
        self.setWindowTitle("ThermalEcho - Print File Listener")
        self.resize(400, 200)

        # Display which directory is being monitored
        self.label = QLabel(f"Monitoring print files in:\n{watch_directory}", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.label)
        
        # Start the file watcher thread
        self.watcher = PrintFileWatcher(watch_directory)
        self.watcher.fileDetected.connect(self.handle_print_file)
        self.watcher.start()

    def handle_print_file(self, content):
        """
        Slot called when a new print file is detected.
        Pops up a dialog displaying the file content.
        """
        dialog = ThermalPrinterSimulator(content, self)
        dialog.exec()

    def closeEvent(self, event):
        # Ensure the watcher thread stops when the application closes.
        self.watcher.stop()
        event.accept()

# -------------------------------
# Main Application Entry Point
# -------------------------------
if __name__ == "__main__":
    # Define the directory to monitor for print files
    watch_directory = "print_jobs"
    if not os.path.exists(watch_directory):
        os.makedirs(watch_directory)

    app = QApplication(sys.argv)
    window = MainWindow(watch_directory)
    window.show()
    sys.exit(app.exec())
