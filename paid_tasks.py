import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from sqlalchemy import and_
from backend import get_session  # Import get_session for session management
from models import Task, Files # Import your SQLAlchemy Task model
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QHBoxLayout, QSpacerItem, QSizePolicy,
    QTabWidget, QFileDialog, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt, QDate
import logging
import os
import shutil
from backend import engine, get_session  # Ensure consistent session management
from google.oauth2.service_account import Credentials 
from googleapiclient.discovery import build 
from googleapiclient.http import MediaFileUpload


SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_service_account_file_path():
    """Dynamically retrieves the path to the service account file."""
    # Get the current directory where the script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))
    
    # The name of the service account file
    service_account_file = os.path.join(script_dir, "adroit-producer-421409-e1fdc9fd2b6f.json")

    # Check if the file exists
    if not os.path.exists(service_account_file):
        raise FileNotFoundError(f"Service account file not found: {service_account_file}")
    
    return service_account_file

# Get the service account file path dynamically
SERVICE_ACCOUNT_FILE = get_service_account_file_path()

def authenticate_google_drive():
    """Authenticate and return the Google Drive service using a service account."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service

class PaidTasksTab(QWidget):
    def __init__(self, tab_widget, parent=None):
        super().__init__(parent)
        self.tab_widget = tab_widget  # Store a reference to the QTabWidget
        self.setWindowTitle('Paid Tasks')
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Search bar for filtering paid tasks
        search_sort_layout = QHBoxLayout()
        self.search_label = QLabel('Search:')
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText('Search paid tasks...')
        self.search_bar.textChanged.connect(self.search_data)
        search_sort_layout.addWidget(self.search_label)
        search_sort_layout.addWidget(self.search_bar)

        layout.addLayout(search_sort_layout)

        # Table to display paid tasks
        self.table = QTableWidget(self)
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            'Name', 'Task Type', 'Date Added', 'Date Finished', 'Price',
            'Status', 'Done By', 'Invoice Sent', 'Invoice Paid', 'Office', 'Files'
        ])
        layout.addWidget(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Load paid tasks
        self.load_paid_tasks()

        # Buttons: Upload Files and Close
        button_layout = QHBoxLayout()

        self.upload_button = QPushButton('Upload Files', self)
        self.upload_button.clicked.connect(self.upload_files)  # Leave the function blank
        button_layout.addWidget(self.upload_button)

        self.close_button = QPushButton('Close', self)
        self.close_button.clicked.connect(self.close_tab)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_paid_tasks(self):
        """Load only the paid tasks from the database."""
        with get_session() as session:
            paid_tasks = session.query(Task).filter_by(status='paid').all()
            self.table.setRowCount(0)  # Clear the table first
            for row, task in enumerate(paid_tasks):
                self.add_task_to_table(task, row)

        # Apply alternating row colors after loading tasks
        self.apply_row_colors()

    def add_task_to_table(self, task, row):
        """Add a paid task to the table."""
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(task.task_name))
        self.table.setItem(row, 1, QTableWidgetItem(task.task_type))
        self.table.setItem(row, 2, QTableWidgetItem(task.date_added.strftime('%Y-%m-%d')))
        self.table.setItem(row, 3, QTableWidgetItem(task.date_finished.strftime('%Y-%m-%d') if task.date_finished else ''))
        self.table.setItem(row, 4, QTableWidgetItem(str(task.price)))
        self.table.setItem(row, 5, QTableWidgetItem(task.status))
        self.table.setItem(row, 6, QTableWidgetItem(task.done_by))
        self.table.setItem(row, 7, QTableWidgetItem('Yes' if task.invoice_sent else 'No'))
        self.table.setItem(row, 8, QTableWidgetItem('Yes' if task.invoice_paid else 'No'))
        self.table.setItem(row, 9, QTableWidgetItem(task.office))
        self.table.setItem(row, 10, QTableWidgetItem(str(task.files_count)))

    def search_data(self):
        """Search and filter paid tasks based on input, and highlight matching rows."""
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
                        item.setBackground(QColor(255, 255, 0, 127))  # Highlight with light yellow
                        match = True
                    else:
                        item.setBackground(original_color)  # Restore original background

            self.table.setRowHidden(row, not match if search_text else False)

    def apply_row_colors(self):
        """Apply alternating colors to table rows."""
        for row in range(self.table.rowCount()):
            color = QColor(220, 220, 220) if row % 2 == 0 else QColor(240, 240, 240)  # Light gray colors
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)
                    item.setData(Qt.UserRole, color)  # Save the original color for search highlight logic

    def close_tab(self):
        """Close the paid tasks tab and remove it from the main tab widget."""
        index = self.tab_widget.indexOf(self)
        if index != -1:
            self.tab_widget.removeTab(index)

    def get_task_id_from_row(self, row):
        """Retrieve the task ID from the selected row."""
        # Assuming the task ID is in the first column (column 0)
        task_id_item = self.table.item(row, 0)
        
        if task_id_item and task_id_item.text().isdigit():
            return int(task_id_item.text())  # Convert task ID to integer and return it
        else:
            return None  # Return None if the ID is invalid or not found

    def upload_files(self):
        """Upload a file for the selected task and save the file details to Google Drive."""
        selected_row = self.table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "No Task Selected", "Please select a task to upload a file.")
            return

        task_id = self.get_task_id_from_row(selected_row)
        task_name_item = self.table.item(selected_row, 1)  # Task name is in column 1
        task_name = task_name_item.text() if task_name_item else None

        if not task_id or not task_name:
            QMessageBox.warning(self, "Invalid Task", "Selected task is invalid.")
            return

        # Open file dialog to select a file
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]  # Get the selected file path

            if not file_path:
                QMessageBox.warning(self, "No File Selected", "Please select a file to upload.")
                return

            file_name = os.path.basename(file_path)

            try:
                service = self.authenticate_google_drive()
                google_drive_file_id = self.upload_file_to_google_drive(service, file_name, file_path)

                if google_drive_file_id:
                    google_drive_link = f"https://drive.google.com/file/d/{google_drive_file_id}/view"
                    
                    # Create a new Files object without a company_id
                    with get_session() as session:
                        new_file = Files(
                            second_id='Task',
                            path=google_drive_link,
                            name=file_name,
                            company_name=task_name,
                            company_id=None  # Set to None for task-related files
                        )

                        session.add(new_file)
                        session.commit()
                        self.update_files_count()
                    QMessageBox.information(self, "File Uploaded", f"File '{file_name}' uploaded successfully for task '{task_name}'.")

            except Exception as e:
                logging.error(f"Failed to upload file to Google Drive for task {task_id}: {str(e)}")
                QMessageBox.critical(self, "Error", f"An error occurred while uploading the file: {str(e)}")

    @staticmethod
    def authenticate_google_drive():
        """Authenticate and return the Google Drive service using a service account."""
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service

    def upload_file_to_google_drive(self, service, file_name, file_path):
        """Upload a file to Google Drive and return the file ID."""
        try:
            folder_id = '15OclGTq9SFDYl9pBA69Gs5-jy2dUwxrZ'

            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }

            media = MediaFileUpload(file_path, mimetype='application/octet-stream')
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            file_id = file.get('id')
            logging.info(f"File '{file_name}' uploaded successfully. File ID: {file_id}")

            # Set file permissions to allow anyone with the link to view
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(fileId=file_id, body=permission).execute()

            return file_id

        except Exception as e:
            logging.error(f"An error occurred while uploading the file to Google Drive: {e}")
            return None
           
    def update_files_count(self):
        """Update the files count for each task."""
        try:
            with get_session() as session:
                tasks = session.query(Task).all()
                for task in tasks:
                    file_count = session.query(Files).filter(and_(Files.company_name == task.task_name, Files.second_id == 'Task')).count()
                    task.files_count = file_count
                session.commit()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while updating file counts: {str(e)}')
            