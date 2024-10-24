from datetime import datetime
import os
import logging
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,QMessageBox
)
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices, QBrush, QColor
from sqlalchemy.exc import SQLAlchemyError
from models import Files, Company
from backend import get_session
from sqlalchemy.orm import joinedload

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_files():
    """Fetch files from the database with error handling for both company-related and task-related files."""
    try:
        with get_session() as session:
            # Fetch all files, including those related to tasks and companies
            files = session.query(Files).options(joinedload(Files.company)).all()

            files_data = []
            for file in files:
                # If the file is related to a company (second_id is 'Company')
                if file.second_id == 'Task':
                    file_data = {
                        'company_id': file.company_id if file.company_id else 'N/A',  # No company association for tasks
                        'company_name': file.company_name,  # Use a placeholder name for task files
                        'second_id': file.second_id,
                        'name': file.name,
                        'path': file.path
                    }
                
                # If the file is related to a task (second_id is 'Task')
                else:
                    file_data = {
                        'company_id': file.company_id if file.company_id else 'N/A',
                        'company_name': file.company_name if file.company_name else 'N/A',
                        'second_id': file.second_id,
                        'name': file.name,
                        'path': file.path
                    }

                files_data.append(file_data)

        return files_data

    except SQLAlchemyError as e:
        logging.error(f"An SQLAlchemy error occurred: {e}")
        return []


def upload_existing_files():
    """Automatically upload existing files from a directory to the database."""
    
    target_dir = "files"
    if not os.path.exists(target_dir):
        logging.info("No files directory found to upload.")
        return

    files_uploaded = 0
    try:
        with get_session() as session:
            for file_name in os.listdir(target_dir):
                target_path = os.path.join(target_dir, file_name)

                # Check if the file already exists in the database
                existing_file = session.query(Files).filter_by(name=file_name).first()

                if not existing_file:
                    # Determine if the file is task-related or company-related based on file naming convention or other logic
                    if "task" in file_name.lower():  # Example: if the file name contains 'task', it's task-related
                        second_id = 'Task'
                        company_id = None  # No company ID for task-related files
                    else:
                        second_id =second_id
                        company_id = company_id  # Modify this logic to associate the file with a company (hardcoded as '1' here)

                    # Create and add the new file record
                    new_file = Files(
                        name=file_name,
                        second_id=second_id,
                        company_id=company_id,
                        path=target_path
                    )
                    session.add(new_file)
                    files_uploaded += 1

            session.commit()
            logging.info(f"{files_uploaded} new files uploaded to the database.")

    except Exception as e:
        logging.exception("Failed to upload existing files")
        QMessageBox.critical(None, "Error", f"An error occurred while uploading files: {e}")


class FilesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = fetch_files()  # Store the fully loaded files data
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Files Management')
        main_layout = QVBoxLayout()

        # Search Bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText('Search...')
        self.search_bar.textChanged.connect(self.search_data)
        main_layout.addWidget(self.search_bar)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(5)  # UTR, Company Name, Type, File Name, Action
        self.table.setHorizontalHeaderLabels(['UTR', 'Company Name', 'Type', 'File Name', 'Action'])
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Set column widths
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 250)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 250)
        self.table.setColumnWidth(4, 100)

        main_layout.addWidget(self.table)

        # Refresh Button
        refresh_button = QPushButton('Refresh', self)
        refresh_button.clicked.connect(self.refresh_data)
        main_layout.addWidget(refresh_button)

        self.load_existing_files()
        self.setLayout(main_layout)

    def load_existing_files(self):
        start_time = time.time()  # Record the start time
        print("Files 1:", datetime.now().strftime("%H:%M:%S"))
    
        """Load files into the table from the fetched data."""
        self.table.setRowCount(0)
        for row, file in enumerate(self.files):
            self.add_file_to_table(file, row)
        self.apply_row_colors()
        
        print("File 2:", datetime.now().strftime("%H:%M:%S"))
        end_time = time.time()  # Record the end time
        print("Total File: {:.2f} seconds".format(end_time - start_time))

    def add_file_to_table(self, file, row, search_text=None):
        """Add a file entry to the table."""
        self.table.insertRow(row)
        # Use dictionary keys to access values in file
        self.table.setItem(row, 0, self.create_noneditable_item(str(file['company_id']), search_text))
        self.table.setItem(row, 1, self.create_noneditable_item(file['company_name'], search_text))
        self.table.setItem(row, 2, self.create_noneditable_item(file['second_id'], search_text))
        self.table.setItem(row, 3, self.create_noneditable_item(file['name'], search_text))

        open_button = QPushButton('Open', self)
        open_button.clicked.connect(lambda checked, file_path=file['path']: self.open_local_file(file_path))
        open_button.setStyleSheet("""
            QPushButton {
                background-color: seagreen;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: lightgreen;
            }
        """)

        self.table.setCellWidget(row, 4, open_button)

    def create_noneditable_item(self, text, search_text):
        """Create a non-editable table item with optional search highlighting."""
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Make item non-editable
        if search_text and search_text in text.lower():
            item.setBackground(QBrush(QColor('lightblue')))
        return item

    def apply_row_colors(self):
        """Apply alternating row colors for better readability."""
        for row in range(self.table.rowCount()):
            color = QColor(230, 230, 250, 127) if row % 2 == 0 else QColor(245, 245, 255, 127)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)

    def search_data(self):
        """Search for text in the table and highlight matching rows."""
        search_text = self.search_bar.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    original_color = item.data(Qt.UserRole)
                    if not original_color:
                        original_color = item.background()
                        item.setData(Qt.UserRole, original_color)

                    if search_text and search_text in item.text().lower():
                        item.setBackground(QColor(255, 255, 0, 127))  # light yellow with transparency
                        match = True
                    else:
                        item.setBackground(original_color)
            self.table.setRowHidden(row, not match if search_text else False)

    def open_local_file(self, file_path):
        """Open a file stored locally using its path or open a Google Drive link."""
        logging.info(f"Trying to open file: {file_path}")

        # Handle Google Drive links
        if 'drive.google.com' in file_path:
            # Ensure the link is in the correct format
            if not file_path.startswith('https://drive.google.com/file/d/'):
                logging.warning("The link does not seem to be a valid Google Drive file link.")
            else:
                # Open the Google Drive link
                QDesktopServices.openUrl(QUrl(file_path))
        else:
            # Treat it as a local file path
            if not os.path.isabs(file_path):
                # Assuming the files are in the same directory as the script
                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)

            # Check if the local file exists
            if os.path.exists(file_path):
                file_url = QUrl.fromLocalFile(file_path)
                logging.info(f"Opening local file with URL: {file_url}")
                QDesktopServices.openUrl(file_url)
            else:
                logging.warning(f"File does not exist: {file_path}")
                # Optionally, display a message box to inform the user

    def refresh_data(self):
        """Refresh the table data from the database."""
        try:
            upload_existing_files()  # Automatically upload existing files
            self.files = fetch_files()  # Re-fetch files from the database
            self.load_existing_files()
            logging.info('The file data has been refreshed successfully.')
        except Exception as e:
            logging.exception("Error occurred during refresh")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FilesTab()
    window.show()
    sys.exit(app.exec_())
